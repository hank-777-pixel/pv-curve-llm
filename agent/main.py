from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

from agent.vector import retriever as _make_retriever
from agent.prompts import get_prompts
from agent.pv_curve.pv_curve import generate_pv_curve

from agent.models.state_models import Inputs
from agent.utils.common_utils import format_inputs_display, create_initial_state
from agent.workflows.compound_workflow import create_compound_workflow
from agent.terminal_ui import divider, info, answer

load_dotenv()

def setup_dependencies():
    """Initialize all dependencies"""
    prompts = get_prompts()
    
    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL") or "pv-curve" or "llama3.1:8b",
        base_url="http://localhost:11434"
    )
    
    retriever = _make_retriever()
    
    return llm, prompts, retriever

def create_graph():
    """Create and return the compiled graph"""
    llm, prompts, retriever = setup_dependencies()
    return create_compound_workflow(llm, prompts, retriever, generate_pv_curve)


def run_agent():
    print("Welcome to the PV Curve Agent! Type 'quit' or 'q' to exit.")    
    llm, prompts, retriever = setup_dependencies()
    graph = create_compound_workflow(llm, prompts, retriever, generate_pv_curve)
    
    print(f"Using model: {llm.model}")
    
    state = create_initial_state()

    while True:
        divider()
        print(f"Current parameters:\n{format_inputs_display(state['inputs'])}")
        divider()

        user_input = input("\nMessage: ")
        if user_input.strip().lower() in ["quit", "q"]:
            info("Quitting...")
            break

        state["messages"] = state.get("messages", []) + [HumanMessage(content=user_input)]
        
        try:
            state = graph.invoke(state)
            
            if state.get("messages") and len(state["messages"]) > 0:
                last_message = state["messages"][-1]
                answer(last_message.content)
        except Exception as e:
            info(f"Error: {e}")
            state["error_info"] = None  # Reset error state

if __name__ == "__main__":
    run_agent()