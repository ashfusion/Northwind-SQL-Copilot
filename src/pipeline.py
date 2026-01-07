import time
import re
from datetime import datetime

from langchain_community.utilities import SQLDatabase
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser

from .models import ExecutionLog, QueryResponse
from .config import (
    SQL_MODEL, NLP_MODEL, NLP_PROMPT_STRATEGY, 
    DB_URI, CACHE_FILE, CACHE_ENABLED,
    get_sql_prompt, get_nlp_prompt
)
from .logger_utils import app_logger
from .cache import CacheManager

class TextToSQLPipeline:
    def __init__(self, use_cache=CACHE_ENABLED):
        app_logger.log_info(f"Initializing Pipeline with NLP strategy: {NLP_PROMPT_STRATEGY}")
        
        self.db = self._connect_to_db()
        self.sql_llm = self._init_llm(SQL_MODEL, temp=0)
        self.nlp_llm = self._init_llm(NLP_MODEL, temp=0.3)
        self.cache = CacheManager(file_path=CACHE_FILE, enabled=use_cache)
        
    def _connect_to_db(self) -> SQLDatabase:
        try:
            db = SQLDatabase.from_uri(DB_URI, sample_rows_in_table_info=2)
            db.get_table_info() 
            app_logger.log_info("Database connected successfully.")
            return db
        except Exception as e:
            app_logger.log_error(f"DB Connection failed: {e}")
            raise

    def _init_llm(self, model_name: str, temp: float):
        return ChatOllama(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=temp
        )

    def _clean_sql(self, query: str) -> str:
        return re.sub(r'```sql|```', '', query, flags=re.IGNORECASE).strip()

    def _sanitize_result(self, raw_result) -> str:
        if not raw_result:
            return "[]"
        if isinstance(raw_result, list) and len(raw_result) > 0:
            if isinstance(raw_result[0], tuple) and len(raw_result[0]) == 1:
                return str(raw_result[0][0])
        return str(raw_result)

    def run(self, question: str) -> QueryResponse:
        log_entry = ExecutionLog(
            timestamp=datetime.now().isoformat(),
            user_prompt=question,
            sql_model=SQL_MODEL,
            nlp_model=NLP_MODEL
        )
        
        start_total = time.time()
        
        # 1. Check Cache
        cached_data = self.cache.get(question)
        if cached_data:
            app_logger.log_info(f"Processing: {question} (Cached)")
            return QueryResponse(
                question=question,
                answer=cached_data['answer'],
                sql_query=cached_data['sql_query'],
                execution_time=0.0,
                from_cache=True
            )

        app_logger.log_info(f"Processing: {question}")

        try:
            # 2. Generate SQL
            t0 = time.time()
            schema = self.db.get_table_info()
            
            sql_prompt_val = get_sql_prompt().invoke({"schema": schema, "question": question})
            log_entry.sql_prompt = sql_prompt_val.to_string()
            
            raw_sql = self.sql_llm.invoke(sql_prompt_val)
            log_entry.sql_query = self._clean_sql(raw_sql.content if hasattr(raw_sql, 'content') else str(raw_sql))
            
            log_entry.sql_generation_time = round(time.time() - t0, 2)
            app_logger.log_info(f"SQL Generated in {log_entry.sql_generation_time}s")

            # 3. Execute SQL
            t0 = time.time()
            try:
                raw_res = self.db.run(log_entry.sql_query)
                log_entry.result = self._sanitize_result(eval(raw_res))
            except Exception as e:
                log_entry.result = "Error executing query"
                raise e
            log_entry.query_execution_time = round(time.time() - t0, 2)

            # 4. Generate Answer
            t0 = time.time()
            nlp_prompt_val = get_nlp_prompt().invoke({
                "question": question,
                "query": log_entry.sql_query,
                "result": log_entry.result
            })
            log_entry.nlp_prompt = nlp_prompt_val.to_string()
            
            ans_res = self.nlp_llm.invoke(nlp_prompt_val)
            log_entry.final_answer = (ans_res.content if hasattr(ans_res, 'content') else str(ans_res)).strip()
            
            log_entry.answer_generation_time = round(time.time() - t0, 2)
            log_entry.success = True
            
            # Save to Cache
            self.cache.set(question, {
                "answer": log_entry.final_answer,
                "sql_query": log_entry.sql_query
            })

        except Exception as e:
            log_entry.error = str(e)
            log_entry.final_answer = f"Error: {str(e)}"
            app_logger.log_error(f"Pipeline Error: {e}")

        finally:
            log_entry.total_duration = round(time.time() - start_total, 2)
            app_logger.log_struct(log_entry)

        return QueryResponse(
            question=question,
            answer=log_entry.final_answer,
            sql_query=log_entry.sql_query or "Failed",
            execution_time=log_entry.total_duration
        )