from typing_extensions import TypedDict, Annotated
from typing import List, Optional, Any
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
    inputs: Any
    results: dict | None
    error_info: dict | None
    plan: Optional[Any]
    current_step: int
    step_results: List[dict]
    is_compound: bool
    retry_count: int
    failed_node: str | None
    conversation_context: List[dict]

