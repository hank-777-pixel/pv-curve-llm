from typing import Dict, Any, List
import uuid
from langchain_core.messages import HumanMessage
from agent.main import setup_dependencies
from agent.workflows.compound_workflow import create_compound_workflow
from agent.models.response_models import ConversationResponse, NodeResponse
from agent.utils.common_utils import create_initial_state
from agent.pv_curve.pv_curve import generate_pv_curve
from agent.output.sinks import MemorySink
from agent.output.context import set_sink, get_sink

class LangGraphAPIManager:
    def __init__(self, provider="ollama"):
        self.provider = provider
        llm, prompts, retriever = setup_dependencies(provider)
        self.graph = create_compound_workflow(llm, prompts, retriever, generate_pv_curve)
        self.active_sessions: Dict[str, Dict] = {}
    
    def process_message(self, message: str, session_id: str = None) -> ConversationResponse:
        """Main API entry point"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get or create session state
        state = self.get_session_state(session_id)
        state["messages"].append(HumanMessage(content=message))
        
        # Track node responses for API
        node_responses = []
        
        prev_sink = get_sink()
        mem_sink = MemorySink()
        set_sink(mem_sink)
        try:
            final_state = self.execute_graph_with_tracking(state, node_responses)
            self.active_sessions[session_id] = final_state
            last_message = final_state["messages"][-1] if final_state["messages"] else None
            progress_messages = mem_sink.get_events()
            return ConversationResponse(
                response_text=last_message.content if last_message else "No response generated",
                node_responses=node_responses,
                updated_state=self.serialize_state(final_state),
                conversation_id=session_id,
                next_suggestions=self.generate_suggestions(final_state),
                progress_messages=progress_messages
            )
        finally:
            set_sink(prev_sink)
    
    def execute_graph_with_tracking(self, state, node_responses):
        """Execute graph while tracking node responses for API"""
        result = self.graph.invoke(state, config={"recursion_limit": 50})
        
        # Collect node responses from the result
        if result.get("node_response"):
            node_responses.append(result["node_response"])
        
        if result.get("collected_node_responses"):
            node_responses.extend(result["collected_node_responses"])
        
        return result
    
    def get_session_state(self, session_id: str):
        """Get existing session or create new one"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        return create_initial_state()
    
    def serialize_state(self, state) -> Dict:
        """Convert state to API-friendly format"""
        return {
            "inputs": state["inputs"].model_dump(),
            "conversation_history": state.get("conversation_history", []),
            "cached_results": state.get("cached_results", []),
            "current_step": state.get("current_step", 0),
            "is_compound": state.get("is_compound", False),
            "step_results": state.get("step_results", []),
            "plan": state.get("plan").model_dump() if state.get("plan") else None,
        }
    
    def generate_suggestions(self, state) -> List[str]:
        """Generate next action suggestions based on current state"""
        suggestions = []
        
        # Base suggestions
        if not state.get("results"):
            suggestions.append("Generate a PV curve")
        
        # Parameter-based suggestions
        inputs = state["inputs"]
        if inputs.grid == "ieee39":
            suggestions.append("Try a different grid system like IEEE 14")
        if inputs.power_factor == 0.95:
            suggestions.append("Change power factor to 0.9")
        if not inputs.capacitive:
            suggestions.append("Switch to capacitive load")
        
        # Conversation-based suggestions
        if state.get("conversation_history"):
            suggestions.append("Ask about voltage stability")
            suggestions.append("Compare with different parameters")
        
        return suggestions[:3]
