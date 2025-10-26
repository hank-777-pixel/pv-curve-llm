from langchain_core.messages import HumanMessage
from datetime import datetime
from typing import Dict, Any, Generator, Tuple

from agent.utils.common_utils import create_initial_state
from agent.history_manager import collect_conversation_context, create_and_save_session

class SessionManager:
    """Manages agent session state and execution."""

    def __init__(self, graph, provider, model_name):
        self.graph = graph
        self.provider = provider
        self.model_name = model_name
        self.state = create_initial_state()
        self.session_start_time = datetime.now()
        self.session_id = f"session_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}"

    def execute_turn_streaming(self, user_input: str, config: Dict[str, Any] = None) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """Execute one turn with streaming updates. Yields (node_name, state_update) tuples."""
        if config is None:
            config = {"recursion_limit": 50}

        self.state["messages"] = self.state.get("messages", []) + [HumanMessage(content=user_input)]

        conversation_context = collect_conversation_context(user_input, self.state, max_exchanges=15)
        self.state["conversation_context"] = conversation_context

        # Stream through the graph execution with stream_mode="updates"
        for chunk in self.graph.stream(self.state, config=config, stream_mode="updates"):
            # Each chunk is a dict with node name as key and state update as value
            # Example: {'compound_classifier': {'is_compound': False, 'node_response': {...}}}
            for node_name, state_update in chunk.items():
                yield (node_name, state_update)
                # Update our state with the changes from this node
                for key, value in state_update.items():
                    if key == "messages":
                        # Append messages instead of replacing
                        self.state["messages"] = self.state.get("messages", []) + value
                    else:
                        self.state[key] = value

        if self.state.get("messages") and len(self.state["messages"]) > 0:
            updated_conversation_context = collect_conversation_context(
                user_input,
                self.state,
                max_exchanges=15
            )
            self.state["conversation_context"] = updated_conversation_context

    def execute_turn(self, user_input: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute one turn of the agent conversation (non-streaming for API compatibility)."""
        # Consume the streaming generator and return final state
        for _ in self.execute_turn_streaming(user_input, config):
            pass
        return self.state

    def save_session(self):
        """Save the current session to history."""
        create_and_save_session(
            self.state,
            self.provider,
            self.model_name,
            self.session_start_time,
            self.session_id
        )

    def get_state(self) -> Dict[str, Any]:
        """Get current session state."""
        return self.state
