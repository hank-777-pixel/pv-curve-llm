from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class NodeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    node_type: str = Field(..., description="Type of node that generated this response")
    success: bool = Field(..., description="Whether the node execution was successful")
    data: Dict[str, Any] = Field(..., description="Node-specific response data")
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(..., description="When this response was generated")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

