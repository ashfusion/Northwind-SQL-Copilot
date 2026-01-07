import os
import logging
import re
from typing import Dict, Any, Optional

# Third-party imports
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TextToSQLPipeline:
    def __init__(self):
        """Initialize database connection and LLMs."""
        self.db = self._connect_to_db()
        
        # Model 1: The Coder (Strong logic/SQL skills)
        self.sql_llm = ChatOllama(
            model=os.getenv("SQL_MODEL", "qwen3-coder:30b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0  # Deterministic for code
        )
        
        # Model 2: The Interpreter (Natural language skills, lightweight)
        self.answer_llm = ChatOllama(
            model=os.getenv("NLP_MODEL", "smollm2:latest"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.7 # Creative for conversation
        )

        self.sql_chain = self._build_sql_chain()
        self.answer_chain = self._build_answer_chain()

    def _connect_to_db(self) -> SQLDatabase:
        """Establishes connection to MySQL database with error handling."""
        try:
            username = os.getenv("DB_USER", "root")
            password = os.getenv("DB_PASS", "pass")
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "3306")
            schema = os.getenv("DB_SCHEMA", "text_to_sql")
            
            uri = f'mysql+pymysql://{username}:{password}@{host}:{port}/{schema}'
            
            logger.info(f"Connecting to database: {schema} at {host}...")
            db = SQLDatabase.from_uri(uri, sample_rows_in_table_info=2)
            
            # Test connection
            db.get_table_info()
            logger.info("Database connection successful.")
            return db
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _get_schema(self, _):
        """Helper to retrieve DB schema."""
        return self.db.get_table_info()

    def _clean_sql_query(self, query: str) -> str:
        """
        Cleans the LLM output to ensure it's a valid SQL query.
        Removes markdown backticks and 'sql' labels.
        """
        cleaned = query.strip()
        # Remove ```sql ... ``` or ``` ... ```
        cleaned = re.sub(r'```sql', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'```', '', cleaned)
        return cleaned.strip()

    def _build_sql_chain(self):
        """Builds the chain responsible for converting Question -> SQL."""
        template = """Based on the table schema below, write a MySQL query that answers the user's question.
        
        RULES:
        1. Output ONLY the SQL query. 
        2. Do not wrap in markdown or code blocks.
        3. Do not include explanations.
        4. Use standard MySQL syntax.

        Table Schema:
        {schema}

        Question: {question}

        SQL Query:
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        return (
            RunnablePassthrough.assign(schema=self._get_schema)
            | prompt
            | self.sql_llm
            | StrOutputParser()
        )

    def _build_answer_chain(self):
        """Builds the chain responsible for converting Result -> Natural Language."""
        template = """You are a helpful data assistant. 
        The user asked: "{question}"
        
        To answer this, we ran the following SQL query:
        {query}
        
        And received this raw data result from the database:
        {result}

        Please provide a natural language answer to the user based on this result. 
        If the result is empty, politely say no data was found.
        Do not mention the internal SQL mechanics unless asked, just give the answer.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        return (
            prompt
            | self.answer_llm
            | StrOutputParser()
        )

    def process_question(self, question: str) -> Dict[str, Any]:
        """Main execution flow: Question -> SQL -> Execution -> Natural Language Answer."""
        logger.info(f"Processing question: {question}")
        
        try:
            # Step 1: Generate SQL
            logger.info("Generating SQL query...")
            raw_sql = self.sql_chain.invoke({"question": question})
            cleaned_sql = self._clean_sql_query(raw_sql)
            logger.info(f"Generated SQL: {cleaned_sql}")

            # Step 2: Execute SQL
            logger.info("Executing SQL query...")
            try:
                # QuerySQLDataBaseTool functionality equivalent
                result = self.db.run(cleaned_sql)
                logger.info(f"Raw Result: {result}")
            except Exception as db_err:
                logger.error(f"SQL Execution failed: {db_err}")
                return {"error": f"SQL Error: {db_err}"}

            # Step 3: Interpret Result with Small LLM
            logger.info("Synthesizing natural language answer...")
            final_answer = self.answer_chain.invoke({
                "question": question,
                "query": cleaned_sql,
                "result": result
            })
            
            logger.info("Process complete.")
            return {
                "question": question,
                "sql_query": cleaned_sql,
                "raw_result": result,
                "answer": final_answer
            }

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Ensure models are pulled in Ollama before running:
    # ollama pull qwen3-coder:30b
    # ollama pull smollm2:latest
    
    pipeline = TextToSQLPipeline()
    
    # Example Query
    user_question = "What is the total 'Line Total' for Geiss Company"
    
    response = pipeline.process_question(user_question)
    
    print("\n" + "="*50)
    if "error" in response:
        print(f"ERROR: {response['error']}")
    else:
        print(f"QUESTION: {response['question']}")
        print(f"SQL     : {response['sql_query']}")
        print(f"ANSWER  : {response['answer']}")
    print("="*50 + "\n")