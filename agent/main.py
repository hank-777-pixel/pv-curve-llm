from langchain_core.messages import HumanMessage
from datetime import datetime

from agent.core import setup_dependencies, create_graph
from agent.utils.common_utils import format_inputs_display, create_initial_state
from agent.terminal_ui import divider, info, answer
from agent.history_manager import collect_conversation_context, create_and_save_session

# Prints the output locally
def local_agent(graph, state, config=None):
    if config is None:
        config = {"recursion_limit": 50}
    
    new_state = graph.invoke(state, config=config)
    
    node_responses = []
    if new_state.get("node_response"):
        node_responses.append(new_state["node_response"])
    
    for key in new_state:
        if key.endswith("_node_response") and new_state[key]:
            node_responses.append(new_state[key])
    
    if node_responses:
        new_state["collected_node_responses"] = node_responses
    
    return new_state


def run_agent():
    print("Welcome to the PV Curve Agent! Type 'quit' or 'q' to exit.")
    
    provider = input("Which model provider would you like to use? Please type 'openai' or 'ollama': ").strip().lower()
    if provider not in ["openai", "ollama"]:
        provider = "ollama"
    
    graph = create_graph(provider)
    llm, _, _ = setup_dependencies(provider)
    
    print(f"Using model: {llm._model_name}")
    
    # Generate unique session ID using timestamp and track session start time
    session_start_time = datetime.now()
    session_id = f"session_{session_start_time.strftime('%Y%m%d_%H%M%S')}"
    state = create_initial_state()

    while True:
        divider()
        lines = format_inputs_display(state["inputs"]).splitlines()
        req_lines = lines[:2]
        opt_lines = lines[2:]
        print("Current parameters:")
        info("Required")
        for ln in req_lines:
            print(f"- {ln}")
        info("Optional")
        for ln in opt_lines:
            print(f"- {ln}")
        divider()
        print("Ask about any input or ask to change its value! i.e. \"What grid systems are available?\" or \"Change the grid system to a 118 bus system\"")

        user_input = input("\nMessage: ")
        if user_input.strip().lower() in ["quit", "q"]:
            info("Quitting...")
            # Save the chat session before exiting
            create_and_save_session(state, provider, llm._model_name, session_start_time, session_id)
            break

        state["messages"] = state.get("messages", []) + [HumanMessage(content=user_input)]
        
        conversation_context = collect_conversation_context(user_input, state, max_exchanges=15)
        state["conversation_context"] = conversation_context
        
        new_state = local_agent(graph, state, config={"recursion_limit": 50})
        
        if new_state.get("messages") and len(new_state["messages"]) > 0:
            last_message = new_state["messages"][-1]
            answer(last_message.content)
            
            updated_conversation_context = collect_conversation_context(user_input, new_state, max_exchanges=15)
            new_state["conversation_context"] = updated_conversation_context
        
        state = new_state

if __name__ == "__main__":
    run_agent()