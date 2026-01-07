from pydantic import BaseModel, Field
from typing import Any, Optional

class ExecutionLog(BaseModel):
    """Structured log entry matching the specific requirements."""
    timestamp: str
    user_prompt: str  # Renamed from question
    
    # Model Configuration
    sql_model: str    # Renamed from sql_model_used
    nlp_model: str    # Renamed from nlp_model_used
    
    # Prompts
    sql_prompt: Optional[str] = None # Renamed from sql_prompt_used
    nlp_prompt: Optional[str] = None # Renamed from nlp_prompt_used
    
    # Execution Artifacts
    sql_query: Optional[str] = None
    result: Optional[str] = None     # Renamed from cleaned_result/raw_result
    final_answer: Optional[str] = None
    
    # Metrics
    sql_generation_time: float = 0.0
    query_execution_time: float = 0.0
    answer_generation_time: float = 0.0
    total_duration: float = 0.0
    
    # Status
    error: Optional[str] = None
    success: bool = False

class QueryResponse(BaseModel):
    """Final response returned to the user."""
    question: str
    answer: str
    sql_query: str
    execution_time: float
    from_cache: bool = False