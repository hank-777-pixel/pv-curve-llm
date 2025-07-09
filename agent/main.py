from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing_extensions import TypedDict, Annotated, Literal
from vector import retriever as _make_retriever
from prompts import get_prompts
from pv_curve.pv_curve import generate_pv_curve
import pandapower.networks as pn
from dotenv import load_dotenv
import os

load_dotenv()

prompts = get_prompts()

# See Modelfile for instructions on how to use a custom model
llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL") or "llama3.1:8b",
    base_url="http://localhost:11434"
)

retriever = _make_retriever()

class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grid: str = "ieee39"            # Test system key (e.g., ieee39)
    bus_id: int = 5                 # Bus to monitor voltage
    step_size: float = 0.01         # Load increment per iteration
    max_scale: float = 3.0          # Max load multiplier
    power_factor: float = 0.95      # Constant power factor
    voltage_limit: float = 0.4      # Voltage threshold to stop
    save_path: str = "generated/pv_curve_voltage_stability.png"  # Output plot path

DEFAULT_INPUTS = Inputs()

class MessageClassifier(BaseModel):
    message_type: Literal["question", "command", "pv_curve"] = Field(
        ...,
        description="Classify if the message requires a tool call/command, a PV-curve generation/run, or a question/request that requires a knowledge response."
    )

# TODO: Experiment with Literals instead
class InputModifier(BaseModel):
    parameter: str = Field(..., description="The parameter to modify")
    value: str | float = Field(..., description="The new value for the parameter")

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
    inputs: Inputs
    results: dict | None

def classify_message(state: State):
    last_message = state["messages"][-1]
    
    # Will automatically run PV curve analysis based on keywords instead of just classification
    # TODO: Evaluate if this is a good heuristic as it could interfere with other questions/requests
    content_lc = last_message.content.strip().lower()
    run_triggers = [
        "run",
        "generate",
        "create",
    ]
    for trig in run_triggers:
        if content_lc == trig or (trig in content_lc and len(content_lc) <= 40):
            print("Classifying input complete")
            return {"message_type": "pv_curve"}

    classifier_llm = llm.with_structured_output(MessageClassifier)

    print("Classifying input...")
    result = classifier_llm.invoke([
        {
            "role": "system",
            "content": prompts["classifier"]["system"]
        },
        {
            "role": "user",
            "content": last_message.content
        }
    ])
    print("Classification complete")

    return {"message_type": result.message_type}

def router(state: State):
    message_type = state.get("message_type", "question")

    if message_type == "command":
        return {"next": "command"}
    if message_type == "pv_curve":
        return {"next": "pv_curve"}
    
    return {"next": "response"}

def response_agent(state: State):
    last_message = state["messages"][-1]

    print("Retrieving context...")
    context = retriever.invoke(last_message.content)
    print("Context retrieved")

    messages = [
        {"role": "system",
         "content": prompts["response_agent"]["system"].format(context=context)},
        {"role": "user", 
         "content": prompts["response_agent"]["user"].format(user_input=last_message.content)}
    ]

    print("Generating response...")
    reply = llm.invoke(messages)
    print("Response generated")
    return {"messages": [reply]}

def command_agent(state: State):
    last_message = state["messages"][-1]
    modifier_llm = llm.with_structured_output(InputModifier)
    
    current_inputs: Inputs = state["inputs"]
    
    print("Modifying inputs...")
    result = modifier_llm.invoke([
        {
            "role": "system",
            "content": prompts["command_agent"]["system"].format(current_inputs=current_inputs)
        },
        {
            "role": "user",
            "content": last_message.content
        }
    ])
    print("Inputs modified")
    
    # Build a new validated Inputs instance. Unknown keys will raise ValidationError.
    try:
        new_inputs = current_inputs.model_copy(update={result.parameter: result.value})
    except ValidationError:
        reply = AIMessage(content=f"Parameter '{result.parameter}' is not recognized. Allowed parameters: {', '.join(Inputs.model_fields.keys())}")
        return {"messages": [reply]}

    reply_content = f"Updated {result.parameter} to {result.value}"
    reply = AIMessage(content=reply_content)
    
    return {"messages": [reply], "inputs": new_inputs}

def pv_curve_agent(state: State):
    print("Generating PV curve...")

    inputs = state["inputs"]

    results = generate_pv_curve(
        grid=inputs.grid,
        target_bus_idx=inputs.bus_id,
        step_size=inputs.step_size,
        max_scale=inputs.max_scale,
        power_factor=inputs.power_factor,
        voltage_limit=inputs.voltage_limit,
        save_path=inputs.save_path,
    )

    print("PV curve generated")
    reply = AIMessage(content=f"PV curve generated and saved to {inputs.save_path}")
    return {"messages": [reply], "results": results}

# TODO: Add RAG, maybe combine with response agent somehow
def analysis_agent(state: State):
    print("Analyzing PV curve results...")
    
    results = state.get("results")
    if not results:
        reply = AIMessage(content="No PV curve results available for analysis.")
        return {"messages": [reply]}
    
    messages = [
        {
            "role": "system",
            "content": prompts["analysis_agent"]["system"].format(results=results)
        },
        {
            "role": "user",
            "content": "Please analyze these PV curve results and provide insights."
        }
    ]
    
    reply = llm.invoke(messages)
    print("Analysis complete")
    return {"messages": [reply]}

graph_builder = StateGraph(State)

graph_builder.add_node("classifier", classify_message)
graph_builder.add_node("router", router)
graph_builder.add_node("response", response_agent)
graph_builder.add_node("command", command_agent)
graph_builder.add_node("pv_curve", pv_curve_agent)
graph_builder.add_node("analysis", analysis_agent)

graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")

graph_builder.add_conditional_edges(
    "router",
    lambda state: state.get("next"),
    {
        "response": "response",
        "command": "command",
        "pv_curve": "pv_curve"
    }
)

graph_builder.add_edge("response", END)
graph_builder.add_edge("command", END)
graph_builder.add_edge("pv_curve", "analysis")
graph_builder.add_edge("analysis", END)

graph = graph_builder.compile()

def run_agent():
    print(f"Using model: {llm.model}")

    state = {"messages": [], "message_type": None, "inputs": Inputs(), "results": None}

    while True:
        print("\nCurrent inputs:")
        for param, value in state["inputs"].model_dump().items():
            print(f"{param}: {value}")
        
        user_input = input("\nMessage: ")
        if user_input == "exit":
            print("Exiting...")
            break

        state["messages"] = state.get("messages", []) + [
            HumanMessage(content=user_input)
        ]

        state = graph.invoke(state)

        if state.get("messages") and len(state["messages"]) > 0:
            last_message = state["messages"][-1]
            print(f"Assistant: {last_message.content}")

if __name__ == "__main__":
    run_agent()