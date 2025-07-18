# For running on Clemson Palmetto HPC
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing_extensions import TypedDict, Annotated, Literal
from typing import Union, List
from vector import retriever as _make_retriever
from prompts import get_prompts
from pv_curve.pv_curve import generate_pv_curve
from dotenv import load_dotenv
import os
# Hugging Face imports
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

# Load DeepSeek-R1 across multiple GPUs using device_map="auto"
model_name = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1")
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
)

# Use pipeline for text generation
llm = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0, max_new_tokens=512)


retriever = _make_retriever()

GridSystem = Literal["ieee14", "ieee24", "ieee30", "ieee39", "ieee57", "ieee118", "ieee300"]

class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grid: GridSystem = "ieee39"
    bus_id: int = Field(default=5, ge=0, le=300)
    step_size: float = Field(default=0.01, gt=0, le=0.1)
    max_scale: float = Field(default=3.0, gt=1.0, le=10.0)
    power_factor: float = Field(default=0.95, gt=0, le=1.0)
    voltage_limit: float = Field(default=0.4, gt=0, le=1.0)
    capacitive: bool = Field(default=False)
    continuation: bool = Field(default=True)

class MessageClassifier(BaseModel):
    message_type: Literal["question", "parameter", "generation"]

class QuestionClassifier(BaseModel):
    question_type: Literal["question_general", "question_parameter"]

InputParameter = Literal["grid", "bus_id", "step_size", "max_scale", "power_factor", "voltage_limit", "capacitive", "continuation"]

class ParameterModification(BaseModel):
    parameter: InputParameter
    value: Union[str, float, int, bool]

class InputModifier(BaseModel):
    modifications: List[ParameterModification]

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
    inputs: Inputs
    results: dict | None
    error_info: dict | None

def hf_invoke(messages):
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    output = llm(prompt)[0]['generated_text']
    response = output.replace(prompt, "").strip()
    return AIMessage(content=response)

def classify_message(state: State):
    result = hf_invoke([
        {"role": "system", "content": prompts["classifier"]["system"]},
        {"role": "user", "content": state["messages"][-1].content}
    ])
    return {"message_type": MessageClassifier.model_validate_json(result.content).message_type}

def router(state: State):
    return {"next": state.get("message_type", "question")}

def question_agent(state: State):
    result = hf_invoke([
        {"role": "system", "content": prompts["question_classifier"]["system"]},
        {"role": "user", "content": state["messages"][-1].content}
    ])
    return {"message_type": QuestionClassifier.model_validate_json(result.content).question_type}

def question_general_agent(state: State):
    context = retriever.invoke(state["messages"][-1].content)
    return {"messages": [hf_invoke([
        {"role": "system", "content": prompts["question_general_agent"]["system"].format(context=context)},
        {"role": "user", "content": prompts["question_general_agent"]["user"].format(user_input=state["messages"][-1].content)}
    ])]}

def question_parameter_agent(state: State):
    return {"messages": [hf_invoke([
        {"role": "system", "content": prompts["question_parameter_agent"]["system"]},
        {"role": "user", "content": state["messages"][-1].content}
    ])]}

def parameter_agent(state: State):
    current_inputs = state["inputs"]
    result = hf_invoke([
        {"role": "system", "content": prompts["parameter_agent"]["system"].format(current_inputs=current_inputs)},
        {"role": "user", "content": state["messages"][-1].content}
    ])
    try:
        parsed = InputModifier.model_validate_json(result.content)
        updates = {}
        for mod in parsed.modifications:
            updates[mod.parameter] = mod.value
        new_inputs = current_inputs.model_copy(update=updates)
        return {"messages": [AIMessage(content=f"Updated: {updates}" )], "inputs": new_inputs}
    except Exception as e:
        return {"error_info": {"error_type": "validation_error", "error_message": str(e)}}

def generation_agent(state: State):
    try:
        results = generate_pv_curve(**state["inputs"].model_dump())
        msg = f"PV curve generated and saved to {results['save_path']}"
        return {"messages": [AIMessage(content=msg)], "results": results}
    except Exception as e:
        return {"error_info": {"error_type": "generation_error", "error_message": str(e)}}

def analysis_agent(state: State):
    context = retriever.invoke("PV curve analysis")
    return {"messages": [hf_invoke([
        {"role": "system", "content": prompts["analysis_agent"]["system"].format(context=context)},
        {"role": "user", "content": prompts["analysis_agent"]["user"].format(results=state["results"], grid_system=state["inputs"].grid)}
    ])]}

def error_handler_agent(state: State):
    return {"messages": [hf_invoke([
        {"role": "system", "content": prompts["error_handler"]["system"]},
        {"role": "user", "content": str(state["error_info"])}
    ])]}

graph_builder = StateGraph(State)

# Nodes
for name, fn in [
    ("classifier", classify_message),
    ("router", router),
    ("question", question_agent),
    ("question_general", question_general_agent),
    ("question_parameter", question_parameter_agent),
    ("parameter", parameter_agent),
    ("generation", generation_agent),
    ("analysis", analysis_agent),
    ("error_handler", error_handler_agent)
]:
    graph_builder.add_node(name, fn)

# Edges
graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")
graph_builder.add_conditional_edges("router", lambda s: s["next"], {
    "question": "question",
    "parameter": "parameter",
    "generation": "generation"
})
graph_builder.add_conditional_edges("question", lambda s: s["message_type"], {
    "question_general": "question_general",
    "question_parameter": "question_parameter"
})
for end in ["question_general", "question_parameter"]:
    graph_builder.add_edge(end, END)
graph_builder.add_edge("generation", "analysis")
graph_builder.add_edge("analysis", END)
graph_builder.add_edge("error_handler", END)
graph_builder.add_conditional_edges("parameter", lambda s: "error_handler" if s.get("error_info") else END, {
    "error_handler": "error_handler",
    END: END
})
graph_builder.add_conditional_edges("generation", lambda s: "error_handler" if s.get("error_info") else "analysis", {
    "error_handler": "error_handler",
    "analysis": "analysis"
})

graph = graph_builder.compile()

def run_agent():
    print(f"Using model: {model_name}")
    state = {"messages": [], "message_type": None, "inputs": Inputs(), "results": None, "error_info": None}
    while True:
        print("\nCurrent inputs:\n", state["inputs"])
        user_input = input("\nMessage: ")
        if user_input.strip().lower() in ["quit", "q"]:
            print("Exiting...")
            break
        state["messages"].append(HumanMessage(content=user_input))
        state = graph.invoke(state)
        if state.get("messages"):
            print("Assistant:", state["messages"][-1].content)

if __name__ == "__main__":
    run_agent()