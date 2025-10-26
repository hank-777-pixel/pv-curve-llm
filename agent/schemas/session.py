from typing import List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ChatSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    session_id: str = Field(..., description="Unique identifier for the chat session")
    start_time: datetime = Field(..., description="When the chat session started")
    end_time: datetime = Field(..., description="When the chat session ended")
    provider: str = Field(..., description="LLM provider used (ollama/openai)")
    model_name: str = Field(..., description="Name of the LLM model used")
    exchanges: List[dict] = Field(default_factory=list, description="Full conversation with all metadata")
    total_exchanges: int = Field(default=0, ge=0, description="Total number of exchanges in the session")
    errors: List[dict] = Field(default_factory=list, description="All errors that occurred during the session")
    final_inputs: dict = Field(default_factory=dict, description="Final parameter state at session end")
    all_results: List[dict] = Field(default_factory=list, description="All PV curve results generated during the session")
    
    total_execution_time_seconds: float = Field(default=0.0, ge=0, description="Total session execution time in seconds")
    parameter_changes_count: int = Field(default=0, ge=0, description="Number of parameter changes made during the session")
    pv_curves_generated_count: int = Field(default=0, ge=0, description="Number of PV curves generated during the session")
    error_count: int = Field(default=0, ge=0, description="Total number of errors that occurred during the session")
    error_types: List[str] = Field(default_factory=list, description="List of unique error types encountered")
    node_execution_counts: dict = Field(default_factory=dict, description="Count of executions for each node type")
    average_response_time_seconds: float = Field(default=0.0, ge=0, description="Average response time per exchange in seconds")
    session_completion_status: str = Field(default="completed", description="Status of session completion")

