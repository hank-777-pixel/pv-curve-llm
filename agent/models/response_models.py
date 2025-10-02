from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class NodeResponse(BaseModel):
    node_type: str
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class ParameterUpdateResponse(BaseModel):
    updated_parameters: List[str]
    current_inputs: Dict[str, Any]
    validation_errors: Optional[List[str]] = None

class PVCurveResponse(BaseModel):
    results_summary: Dict[str, Any]
    plot_path: str
    analysis: Optional[str] = None
    performance_metrics: Dict[str, Any]

class ConversationResponse(BaseModel):
    response_text: str
    node_responses: List[NodeResponse]
    updated_state: Dict[str, Any]
    conversation_id: str
    next_suggestions: Optional[List[str]] = None
    progress_messages: Optional[List[Dict[str, Any]]] = None