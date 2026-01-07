from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from agent.vector import retriever as _make_retriever
from agent.prompts import get_prompts
from agent.pv_curve.pv_curve import generate_pv_curve
from agent.workflows.workflow import create_workflow

load_dotenv()

<<<<<<< HEAD
def setup_dependencies(provider="openai"):
=======
def setup_dependencies(provider="ollama"):
>>>>>>> 09e35b4 (merge from master)
    """Setup LLM, prompts, and retriever based on provider."""
    prompts = get_prompts()

    if provider == "openai":
        llm = ChatOpenAI(
            model="gpt-5-mini-2025-08-07",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        llm._model_name = "gpt-5-mini-2025-08-07"
    else:
        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL") or "pv-curve" or "llama3.1:8b",
<<<<<<< HEAD
            base_url="http://localhost:11434"
=======
            base_url="http://localhost:11434",
            timeout=300.0  # Increase timeout to 5 minutes for long-running analysis
>>>>>>> 09e35b4 (merge from master)
        )
        llm._model_name = llm.model

    retriever = _make_retriever()

    return llm, prompts, retriever

def create_graph(provider="ollama"):
    """Create the LangGraph workflow."""
    llm, prompts, retriever = setup_dependencies(provider)
    return create_workflow(llm, prompts, retriever, generate_pv_curve)
