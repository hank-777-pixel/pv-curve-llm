from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProgressEvent(BaseModel):
    id: str
    type: Literal[
        "info",
        "answer",
        "spinner_start",
        "spinner_update",
        "spinner_end",
        "error",
        "step_started",
        "step_completed",
    ]
    text: Optional[str] = None
    node: Optional[str] = None
    step: Optional[int] = None
    ts: datetime
    level: Literal["debug", "info", "warn", "error"] = "info"
    spinner_id: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


