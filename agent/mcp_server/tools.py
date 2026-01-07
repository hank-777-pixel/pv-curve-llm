"""MCP tool wrappers for PV Curve Agent nodes."""
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend - no GUI, renders to files only

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from agent.mcp_server.state_manager import state_manager
from agent.core import setup_dependencies
from agent.pv_curve.pv_curve import generate_pv_curve
import os

# Import all node functions
from agent.nodes.classify import classify_message
from agent.nodes.route import router
from agent.nodes.question_general import question_general_agent
from agent.nodes.question_parameter import question_parameter_agent
from agent.nodes.parameter import parameter_agent
from agent.nodes.generation import generation_agent
from agent.nodes.planner import planner_agent
from agent.nodes.step_controller import step_controller
from agent.nodes.advance_step import advance_step
from agent.nodes.error_handler import error_handler_agent
from agent.nodes.summary import summary_agent

# Initialize dependencies once (shared across all tools)
# This is more efficient than creating them for each tool call
_llm, _prompts, _retriever = setup_dependencies("ollama")


def classify_message_tool(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Classify user message into one of: question_general, question_parameter, parameter, generation.
    
    Args:
        user_message: The user's input message to classify
        session_id: Unique session identifier
        
    Returns:
        Dict with message_type and updated state
    """
    # Get state for this session
    state = state_manager.get_state(session_id)
    
    # Add user message to state (classify needs it)
    state["messages"].append(HumanMessage(content=user_message))
    
    # Call the original classify_message function
    updates = classify_message(state, _llm, _prompts)
    
    # Update state with classification results
    state_manager.update_state(session_id, updates)
    
    # Get updated state and serialize
    updated_state = state_manager.get_state(session_id)
    
    return {
        "message_type": updates.get("message_type"),
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def route_request_tool(session_id: str) -> Dict[str, Any]:
    """
    Route the current request to the appropriate next tool.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict with next_tool, is_compound, reasoning, and updated state
    """
    state = state_manager.get_state(session_id)
    
    # Call the original router function
    updates = router(state)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state
    updated_state = state_manager.get_state(session_id)
    
    # Extract reasoning from node_response
    node_response = updates.get("node_response", {})
    reasoning = node_response.get("message", "") if hasattr(node_response, "get") else str(node_response)
    
    return {
        "next_tool": updates.get("next"),
        "is_compound": updates.get("is_compound", False),
        "reasoning": reasoning,
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def question_general_tool(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Answer general questions about power systems and PV curves using RAG.
    
    Args:
        user_message: The user's question
        session_id: Unique session identifier
        
    Returns:
        Dict with response and updated state
    """
    state = state_manager.get_state(session_id)
    
    # Add user message if not already there
    if not state.get("messages") or state["messages"][-1].content != user_message:
        state["messages"].append(HumanMessage(content=user_message))
    
    # Call the original node function
    updates = question_general_agent(state, _llm, _prompts, _retriever)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state and extract response
    updated_state = state_manager.get_state(session_id)
    last_message = updated_state["messages"][-1] if updated_state.get("messages") else None
    response_text = last_message.content if last_message and hasattr(last_message, 'content') else ""
    
    return {
        "response": response_text,
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def question_parameter_tool(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Answer questions about input parameters and their effects.
    
    Args:
        user_message: The user's question about parameters
        session_id: Unique session identifier
        
    Returns:
        Dict with response and updated state
    """
    state = state_manager.get_state(session_id)
    
    # Add user message if not already there
    if not state.get("messages") or state["messages"][-1].content != user_message:
        state["messages"].append(HumanMessage(content=user_message))
    
    # Call the original node function
    updates = question_parameter_agent(state, _llm, _prompts)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state and extract response
    updated_state = state_manager.get_state(session_id)
    last_message = updated_state["messages"][-1] if updated_state.get("messages") else None
    response_text = last_message.content if last_message and hasattr(last_message, 'content') else ""
    
    return {
        "response": response_text,
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def modify_parameters_tool(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Modify input parameters based on user request.
    
    Args:
        user_message: User's parameter modification request
        session_id: Unique session identifier
        
    Returns:
        Dict with updated parameters and state
    """
    state = state_manager.get_state(session_id)
    
    # Add user message if not already there
    if not state.get("messages") or state["messages"][-1].content != user_message:
        state["messages"].append(HumanMessage(content=user_message))
    
    # Call the original node function
    updates = parameter_agent(state, _llm, _prompts)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state
    updated_state = state_manager.get_state(session_id)
    
    # Extract updated parameters from node_response
    node_response = updates.get("node_response", {})
    response_data = node_response.get("data", {}) if hasattr(node_response, "get") else {}
    updated_parameters = response_data.get("updated_parameters", []) if isinstance(response_data, dict) else []
    
    # Get current inputs
    current_inputs = updated_state["inputs"]
    inputs_dict = current_inputs.model_dump() if hasattr(current_inputs, "model_dump") else current_inputs
    
    return {
        "updated_parameters": updated_parameters,
        "current_inputs": inputs_dict,
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def generate_pv_curve_tool(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Generate PV curve analysis for the current system configuration.
    
    Args:
        user_message: User's generation request (optional, can include parameters)
        session_id: Unique session identifier
        
    Returns:
        Dict with PV curve results and updated state
    """
    try:
        # Auto-detect writable directory for Claude Desktop if env var not set
        if not os.getenv("PV_CURVE_OUTPUT_DIR"):
            # Try to use project's generated folder first (if writable)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_generated = os.path.join(project_root, "generated")
            
            # Check if project's generated folder is writable
            if os.access(project_root, os.W_OK):
                os.environ["PV_CURVE_OUTPUT_DIR"] = project_generated
            else:
                # Fall back to user's home directory
                home_dir = os.path.expanduser("~")
                home_output = os.path.join(home_dir, "pv_curve_output")
                os.makedirs(home_output, exist_ok=True)
                os.environ["PV_CURVE_OUTPUT_DIR"] = home_output
        
        # Set flag to skip blocking plt.show() in MCP context (avoids hanging)
        os.environ["PV_CURVE_SKIP_SHOW"] = "1"
        
        # Create fresh LLM instance for this call
        llm, prompts, retriever = setup_dependencies("ollama")
        
        state = state_manager.get_state(session_id)
        
        # Add user message if provided and not already there
        if user_message and (not state.get("messages") or state["messages"][-1].content != user_message):
            state["messages"].append(HumanMessage(content=user_message))
        
        # Call the original node function
<<<<<<< HEAD
        updates = generation_agent(state, llm, prompts, retriever, generate_pv_curve)
=======
        print(f"DEBUG: About to call generation_agent")
        updates = generation_agent(state, llm, prompts, retriever, generate_pv_curve)
        print(f"DEBUG: generation_agent completed")
>>>>>>> 09e35b4 (merge from master)
        
        # Update state
        state_manager.update_state(session_id, updates)
        
        # Get updated state
        updated_state = state_manager.get_state(session_id)
        
        # Extract response and results
        last_message = updated_state["messages"][-1] if updated_state.get("messages") else None
        response_text = last_message.content if last_message and hasattr(last_message, 'content') else ""
        results = updated_state.get("results") or {}
        
        # Build a clickable file:// URL for the image
        image_file_url = None
        save_path = results.get("save_path")
        if save_path:
            # If save_path is already absolute, use it directly
            if os.path.isabs(save_path):
                absolute_path = save_path
            else:
                # Otherwise, resolve relative to project root
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                absolute_path = os.path.join(project_root, save_path)
            absolute_path = os.path.abspath(absolute_path)
            image_file_url = f"file://{absolute_path}"
        
        return {
            "results": results,
            "response": response_text,
            "image_file_url": image_file_url,
            "state": state_manager.serialize_state(updated_state),
            "success": True
        }
        
    except Exception as e:
        # Catch ALL exceptions from anywhere in the function
        error_message = f"Error generating PV curve: {str(e)}"
        
        # Try to get state for error response, but handle if that fails too
        try:
            updated_state = state_manager.get_state(session_id)
            state_serialized = state_manager.serialize_state(updated_state)
        except:
            state_serialized = {}
        
        return {
            "results": None,
            "response": error_message,
            "image_file_url": None,
            "state": state_serialized,
            "success": False,
            "error": str(e)
        }
def plan_steps_tool(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Create a multi-step plan for complex requests.
    
    Args:
        user_message: User's complex multi-step request
        session_id: Unique session identifier
        
    Returns:
        Dict with plan and updated state
    """
    state = state_manager.get_state(session_id)
    
    # Add user message if not already there
    if not state.get("messages") or state["messages"][-1].content != user_message:
        state["messages"].append(HumanMessage(content=user_message))
    
    # Call the original node function
    updates = planner_agent(state, _llm, _prompts)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state
    updated_state = state_manager.get_state(session_id)
    plan = updated_state.get("plan")
    
    # Serialize plan if it's a Pydantic model
    plan_dict = plan.model_dump() if plan and hasattr(plan, "model_dump") else plan
    
    return {
        "plan": plan_dict,
        "steps_count": len(plan.steps) if plan else 0,
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def step_controller_tool(session_id: str) -> Dict[str, Any]:
    """
    Execute the current step in a multi-step plan.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict with next_tool, current_step, step_info, and updated state
    """
    state = state_manager.get_state(session_id)
    
    # Call the original node function
    updates = step_controller(state)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state
    updated_state = state_manager.get_state(session_id)
    
    # Extract step info from node_response
    node_response = updates.get("node_response", {})
    step_info = {}
    if hasattr(node_response, "get"):
        step_info = node_response.get("data", {})
    elif isinstance(node_response, dict):
        step_info = node_response.get("data", {})
    
    return {
        "next_tool": updates.get("next"),
        "current_step": updated_state.get("current_step", 0),
        "step_info": step_info,
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def advance_step_tool(session_id: str) -> Dict[str, Any]:
    """
    Advance to the next step in a multi-step plan.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict with next_tool, current_step, and updated state
    """
    state = state_manager.get_state(session_id)
    
    # Call the original node function
    updates = advance_step(state)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state
    updated_state = state_manager.get_state(session_id)
    
    return {
        "next_tool": updates.get("next"),
        "current_step": updated_state.get("current_step", 0),
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def handle_error_tool(session_id: str) -> Dict[str, Any]:
    """
    Handle errors and attempt recovery.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict with error resolution and updated state
    """
    state = state_manager.get_state(session_id)
    
    # Call the original node function
    updates = error_handler_agent(state, _llm, _prompts)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state
    updated_state = state_manager.get_state(session_id)
    
    # Extract response
    last_message = updated_state["messages"][-1] if updated_state.get("messages") else None
    response_text = last_message.content if last_message and hasattr(last_message, 'content') else ""
    
    return {
        "response": response_text,
        "retry_node": updates.get("retry_node"),
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }


def summarize_results_tool(session_id: str) -> Dict[str, Any]:
    """
    Summarize results from a completed multi-step workflow.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict with summary and updated state
    """
    state = state_manager.get_state(session_id)
    
    # Call the original node function
    updates = summary_agent(state)
    
    # Update state
    state_manager.update_state(session_id, updates)
    
    # Get updated state
    updated_state = state_manager.get_state(session_id)
    
    # Extract summary
    last_message = updated_state["messages"][-1] if updated_state.get("messages") else None
    summary_text = last_message.content if last_message and hasattr(last_message, 'content') else ""
    
    return {
        "summary": summary_text,
        "state": state_manager.serialize_state(updated_state),
        "success": True
    }