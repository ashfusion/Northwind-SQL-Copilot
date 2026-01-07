import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# --- Global Configuration ---
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_FILE = "query_cache.json"

SQL_MODEL = os.getenv("SQL_MODEL", "hf.co/StellaYoon/data-sql-7b-oracle-postgresql-v2:Q5_K_M")
NLP_MODEL = os.getenv("NLP_MODEL", "smollm2:latest")
# Renamed from NLP_MODEL_TYPE
NLP_PROMPT_STRATEGY = os.getenv("NLP_PROMPT", "short") 

DB_SCHEMA = os.getenv("DB_SCHEMA", "text_to_sql")
DB_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{DB_SCHEMA}"

# --- SQL Prompts ---
SQL_TEMPLATE = """Based on the table schema below, write a MySQL query that answers the user's question.

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

# --- Natural Language Prompts ---

NLP_PROMPT_SHORT = """You are a financial data assistant.
User Question: "{question}"

Context:
- SQL Query Run: {query}
- Data Returned: {result}

Instructions:
1. Answer the user's question using the Data Returned.
2. FORMATTING RULE: Format all currency values in USD (e.g., $1,000). Do NOT show decimal points (round to nearest dollar).
3. If the Data Returned is empty or contains "[]", state that no records were found.
4. Be concise and professional.
"""

NLP_PROMPT_TINY = """Task: Answer based on Data.
Question: {question}
Data: {result}

Rules:
1. If Data is "[]" or "None", say "No data found."
2. FORMATTING: Show money in USD (e.g. $500). NO decimals.
3. Do not explain the SQL.
"""

def get_nlp_prompt() -> ChatPromptTemplate:
    """Factory to get the appropriate prompt template based on strategy."""
    if NLP_PROMPT_STRATEGY.lower() == "tiny":
        return ChatPromptTemplate.from_template(NLP_PROMPT_TINY)
    return ChatPromptTemplate.from_template(NLP_PROMPT_SHORT)

def get_sql_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(SQL_TEMPLATE)