from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ConversationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    response_text: str = Field(..., description="Main response text")
    node_responses: List[Dict[str, Any]] = Field(default_factory=list, description="Responses from each node")
    updated_state: Dict[str, Any] = Field(default_factory=dict, description="Updated state after processing")
    conversation_id: str = Field(..., description="Session/conversation ID")
    next_suggestions: List[str] = Field(default_factory=list, description="Suggested next actions")
    progress_messages: List[Dict[str, Any]] = Field(default_factory=list, description="Progress/status messages")

