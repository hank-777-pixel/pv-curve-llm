from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing_extensions import TypedDict, Annotated, Literal
from typing import Union, List
from vector import retriever as _make_retriever
from prompts import get_prompts
from pv_curve.pv_curve import generate_pv_curve
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

# Define allowed grid systems
GridSystem = Literal["ieee14", "ieee24", "ieee30", "ieee39", "ieee57", "ieee118", "ieee300"]

class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grid: GridSystem = "ieee39"
    bus_id: int = Field(default=5, ge=0, le=300)  # Bus to monitor voltage (0-300 range)
    step_size: float = Field(default=0.01, gt=0, le=0.1)  # Load increment per iteration
    max_scale: float = Field(default=3.0, gt=1.0, le=10.0)  # Max load multiplier
    power_factor: float = Field(default=0.95, gt=0, le=1.0)  # Constant power factor
    voltage_limit: float = Field(default=0.4, gt=0, le=1.0)  # Voltage threshold to stop
    capacitive: bool = Field(default=False)  # Whether load is capacitive or inductive
    continuation: bool = Field(default=True)  # Whether to show mirrored curve
    save_path: str = "generated/pv_curve_voltage_stability.png"  # Output plot path

class MessageClassifier(BaseModel):
    message_type: Literal["question", "command", "pv_curve"] = Field(
        ...,
        description="Classify if the message requires a tool call/command, a PV-curve generation/run, or a question/request that requires a knowledge response."
    )

InputParameter = Literal["grid", "bus_id", "step_size", "max_scale", "power_factor", "voltage_limit", "capacitive", "continuation", "save_path"]

class ParameterModification(BaseModel):
    parameter: InputParameter = Field(..., description="The parameter to modify")
    value: Union[str, float, int, bool] = Field(..., description="The new value for the parameter")

class InputModifier(BaseModel):
    modifications: List[ParameterModification] = Field(..., description="List of parameter modifications to apply")

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
    inputs: Inputs
    results: dict | None

def classify_message(state: State):
    last_message = state["messages"][-1]
    
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
    try:
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
    except Exception as e:
        reply = AIMessage(content=f"Error parsing command: {str(e)}. Please specify valid parameters and values.")
        return {"messages": [reply]}
    
    try:
        updates = {}
        reply_parts = []
        
        for modification in result.modifications:
            converted_value = modification.value
            if modification.parameter in ["bus_id"]:
                converted_value = int(modification.value)
            elif modification.parameter in ["step_size", "max_scale", "power_factor", "voltage_limit"]:
                converted_value = float(modification.value)
            elif modification.parameter in ["capacitive", "continuation"]:
                if isinstance(modification.value, str):
                    converted_value = modification.value.lower() in ["true", "yes", "1", "on"]
                else:
                    converted_value = bool(modification.value)
            
            updates[modification.parameter] = converted_value
            
            param_msg = f"{modification.parameter} to {converted_value}"
            if modification.parameter == "grid":
                param_msg += f" (Grid system changed)"
            elif modification.parameter == "bus_id":
                param_msg += f" (Monitoring bus)"
            reply_parts.append(param_msg)
        
        new_inputs = current_inputs.model_copy(update=updates)
        

        if len(reply_parts) == 1:
            reply_content = f"Updated {reply_parts[0]}"
        else:
            reply_content = f"Updated {len(reply_parts)} parameters:\n" + "\n".join(f"• {part}" for part in reply_parts)
        
        reply = AIMessage(content=reply_content)
        return {"messages": [reply], "inputs": new_inputs}
        
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = error.get('loc', ['unknown'])[0]
            msg = error.get('msg', 'Invalid value')
            error_details.append(f"{field}: {msg}")
        
        reply = AIMessage(content=f"Validation errors: {'; '.join(error_details)}")
        return {"messages": [reply]}
    except ValueError as e:
        reply = AIMessage(content=f"Type conversion error: {str(e)}")
        return {"messages": [reply]}

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
        capacitive=inputs.capacitive,
        continuation=inputs.continuation,
        save_path=inputs.save_path,
    )

    print("PV curve generated")
    
    # Enhanced response with key parameters
    load_type = "capacitive" if inputs.capacitive else "inductive"
    curve_type = "with continuation curve" if inputs.continuation else "upper branch only"
    
    reply_content = (
        f"PV curve generated for {inputs.grid.upper()} system (Bus {inputs.bus_id})\n"
        f"Load type: {load_type}, Power factor: {inputs.power_factor}\n"
        f"Plot saved to {inputs.save_path} ({curve_type})"
    )
    
    reply = AIMessage(content=reply_content)
    return {"messages": [reply], "results": results}

def analysis_agent(state: State):
    print("Analyzing PV curve results...")
    
    results = state.get("results")
    if not results:
        reply = AIMessage(content="No PV curve results available for analysis.")
        return {"messages": [reply]}
    
    inputs = state["inputs"]
    analysis_query = (
        f"PV curve voltage stability analysis nose point load margin "
        f"voltage drop {inputs.grid} power system stability assessment "
        f"power factor {inputs.power_factor} voltage collapse"
    )
    
    print("Retrieving analysis context...")
    context = retriever.invoke(analysis_query)
    print("Analysis context retrieved")
    
    messages = [
        {
            "role": "system",
            "content": prompts["analysis_agent"]["system"].format(
                context=context, 
                results=results
            )
        },
        {
            "role": "user",
            "content": prompts["analysis_agent"]["user"]
        }
    ]
    
    print("Generating analysis...")
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