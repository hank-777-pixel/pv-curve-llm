from typing_extensions import TypedDict, Annotated, Literal
from typing import Union, List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from datetime import datetime

GridSystem = Literal["ieee14", "ieee24", "ieee30", "ieee39", "ieee57", "ieee118", "ieee300"]
InputParameter = Literal["grid", "bus_id", "step_size", "max_scale", "power_factor", "voltage_limit", "capacitive", "continuation"]

class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grid: GridSystem = "ieee39"
    bus_id: int = Field(default=5, ge=0, le=300)
    step_size: float = Field(default=0.01, gt=0, le=0.1)
    max_scale: float = Field(default=3.0, gt=1.0, le=10.0)
    power_factor: float = Field(default=0.95, gt=0, le=1.0)
    voltage_limit: float = Field(default=0.4, gt=0, le=1.0)
    capacitive: bool = Field(default=False)
    continuation: bool = Field(default=True)

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
    inputs: Inputs
    results: dict | None
    error_info: dict | None
    plan: Optional[Any]  # MultiStepPlan type
    current_step: int
    step_results: List[dict]
    is_compound: bool
    retry_count: int
    failed_node: str | None
    conversation_history: List[dict]
    cached_results: List[dict]
    # New fields for context-aware nodes
    needs_history: bool
    conversation_context: List[dict]
    context_window_size: int



class ChatSession(BaseModel):
    """Model for archiving complete chat sessions with full metadata"""
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
    
    # Session metadata fields
    total_execution_time_seconds: float = Field(default=0.0, ge=0, description="Total session execution time in seconds")
    parameter_changes_count: int = Field(default=0, ge=0, description="Number of parameter changes made during the session")
    pv_curves_generated_count: int = Field(default=0, ge=0, description="Number of PV curves generated during the session")
    error_count: int = Field(default=0, ge=0, description="Total number of errors that occurred during the session")
    error_types: List[str] = Field(default_factory=list, description="List of unique error types encountered")
    node_execution_counts: dict = Field(default_factory=dict, description="Count of executions for each node type")
    average_response_time_seconds: float = Field(default=0.0, ge=0, description="Average response time per exchange in seconds")
    session_completion_status: str = Field(default="completed", description="Status of session completion") 