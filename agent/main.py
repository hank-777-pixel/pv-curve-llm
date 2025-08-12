from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
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

def setup_dependencies(provider="ollama"):
    prompts = get_prompts()
    
    if provider == "openai":
        llm = ChatOpenAI(
            model="o3-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        llm._model_name = "o3-mini"
    else:
        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL") or "pv-curve" or "llama3.1:8b",
            base_url="http://localhost:11434"
        )
        llm._model_name = llm.model
    
    retriever = _make_retriever()
    
    return llm, prompts, retriever

def create_graph(provider="ollama"):
    llm, prompts, retriever = setup_dependencies(provider)
    return create_compound_workflow(llm, prompts, retriever, generate_pv_curve)


def run_agent():
    print("Welcome to the PV Curve Agent! Type 'quit' or 'q' to exit.")
    
    provider = input("Which model provider would you like to use? Please type 'openai' or 'ollama': ").strip().lower()
    if provider not in ["openai", "ollama"]:
        provider = "ollama"
    
    llm, prompts, retriever = setup_dependencies(provider)
    graph = create_compound_workflow(llm, prompts, retriever, generate_pv_curve)
    
    print(f"Using model: {llm._model_name}")
    
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
            new_state = graph.invoke(state, config={"recursion_limit": 50})
            
            if new_state.get("messages") and len(new_state["messages"]) > 0:
                last_message = new_state["messages"][-1]
                answer(last_message.content)
                
                conversation_history = state.get("conversation_history", [])
                conversation_history.append({
                    "user_input": user_input,
                    "assistant_response": last_message.content,
                    "inputs_used": new_state["inputs"].model_dump()
                })
                if len(conversation_history) > 10:
                    conversation_history = conversation_history[-10:]
                
                if new_state.get("results"):
                    cached_results = state.get("cached_results", [])
                    cached_results.append({
                        "inputs": new_state["inputs"].model_dump(),
                        "results": new_state["results"],
                        "timestamp": user_input
                    })
                    if len(cached_results) > 5:
                        cached_results = cached_results[-5:]
                    new_state["cached_results"] = cached_results
                
                new_state["conversation_history"] = conversation_history
            
            state = new_state
        except Exception as e:
            info(f"Error: {e}")
            state["error_info"] = None

if __name__ == "__main__":
    run_agent()