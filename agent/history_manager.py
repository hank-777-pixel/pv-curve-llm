"""
History Manager for Chat Session Archival

This module handles saving chat sessions to persistent storage.
It creates a /history folder and saves complete session data as JSON files.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from agent.models.state_models import ChatSession


def ensure_history_folder():
    """
    Ensure the history folder exists, create it if it doesn't.
    
    Returns:
        str: Path to the history folder
    """
    # Get the project root directory (where this file is located)
    current_dir = Path(__file__).parent.parent  # Go up from agent/ to project root
    history_folder = current_dir / "history"
    
    # Create the folder if it doesn't exist
    history_folder.mkdir(exist_ok=True)
    
    return str(history_folder)

def save_session(session_data: Dict[str, Any], session_id: str) -> str:
    """
    Save a chat session to an individual JSON file.
    
    Args:
        session_data: Complete session data (ChatSession model data)
        session_id: Unique identifier for the session
        
    Returns:
        str: Path to the saved file
        
    Raises:
        Exception: If there's an error saving the file
    """
    try:
        # Ensure history folder exists
        history_folder = ensure_history_folder()
        
        # Create filename with timestamp and session ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"chat_session_{session_id}_{timestamp}.json"
        filepath = os.path.join(history_folder, filename)
        
        # Convert session data to the new format
        session_data_formatted = convert_session_to_new_format(session_data, session_id)
        
        # Save session to individual file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data_formatted, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
        
    except Exception as e:
        raise Exception(f"Failed to save session {session_id}: {str(e)}")



def convert_session_to_new_format(session_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """
    Convert session data from ChatSession format to the new consolidated format.
    
    Args:
        session_data: Raw session data from ChatSession
        session_id: Session identifier
        
    Returns:
        Dict[str, Any]: Session data in new format
    """
    # Extract basic session info
    provider = session_data.get("provider", "unknown")
    model_name = session_data.get("model_name", "unknown")
    start_time = session_data.get("start_time", datetime.now().isoformat())
    end_time = session_data.get("end_time", datetime.now().isoformat())
    
    # Create session name
    session_name = f"PV_Curve_Session_{provider}"
    
    # Convert exchanges to messages format
    messages = []
    
    for exchange in session_data.get("exchanges", []):
        # Create message entry
        message = {
            "timestamp": exchange.get("timestamp", datetime.now().isoformat()),
            "user_input": exchange.get("user_input", ""),
            "assistant_response": exchange.get("assistant_response", ""),
            "inputs_used": exchange.get("inputs_state", {})
        }
        messages.append(message)
    
    # Extract cached results (simplified for now)
    cached_results = []
    
    # Create session metadata
    metadata = {
        "total_messages": len(messages),
        "total_cached_results": len(cached_results)
    }
    
    # Create new session format
    new_session = {
        "session_id": session_id,
        "session_name": session_name,
        "created_at": start_time,
        "last_updated": end_time,
        "messages": messages,
        "cached_results": cached_results,
        "metadata": metadata
    }
    
    return new_session

def collect_conversation_context(user_input: str, new_state: dict, max_exchanges: int = 15):
    """
    Collect essential conversation context after each agent response.
    
    Args:
        user_input: The user's input message
        new_state: The state returned by the agent
        max_exchanges: Maximum number of exchanges to keep in memory
        
    Returns:
        list: List of exchange dictionaries with essential data only
    """
    # Get the assistant's response
    assistant_response = ""
    if new_state.get("messages") and len(new_state["messages"]) > 0:
        assistant_response = new_state["messages"][-1].content
    
    # Create simplified exchange data with only essential information
    exchange_data = {
        "user_input": user_input,
        "assistant_response": assistant_response,
        "timestamp": datetime.now().isoformat(),
        "message_type": new_state.get("message_type"),
        "inputs_state": new_state.get("inputs", {}).model_dump() if hasattr(new_state.get("inputs"), 'model_dump') else new_state.get("inputs", {}),
        "results": new_state.get("results"),
        "error_info": new_state.get("error_info")
    }
    
    # Get existing conversation context
    conversation_context = new_state.get("conversation_context", [])
    
    # Add new exchange
    conversation_context.append(exchange_data)
    
    # Limit context window for performance
    if len(conversation_context) > max_exchanges:
        conversation_context = conversation_context[-max_exchanges:]
    
    return conversation_context

def calculate_session_metadata(state: dict, session_start_time: datetime) -> dict:
    """
    Calculate comprehensive session metadata from conversation context.
    
    Args:
        state: Current conversation state
        session_start_time: When the session started
        
    Returns:
        dict: Calculated metadata including execution time, counts, and statistics
    """
    conversation_context = state.get("conversation_context", [])
    end_time = datetime.now()
    
    # Calculate total execution time
    total_execution_time = (end_time - session_start_time).total_seconds()
    
    # Count parameter changes
    parameter_changes_count = 0
    for exchange in conversation_context:
        if exchange.get("message_type") == "parameter_change":
            parameter_changes_count += 1
    
    # Count PV curves generated
    pv_curves_generated_count = 0
    for exchange in conversation_context:
        if exchange.get("results") and exchange.get("message_type") in ["analysis", "pv_curve"]:
            pv_curves_generated_count += 1
    
    # Count errors and collect error types
    error_count = 0
    error_types = []
    for exchange in conversation_context:
        if exchange.get("error_info"):
            error_count += 1
            error_type = exchange["error_info"].get("error_type", "unknown")
            if error_type not in error_types:
                error_types.append(error_type)
    
    # Count node executions
    node_execution_counts = {}
    for exchange in conversation_context:
        node_responses = exchange.get("node_responses", [])
        for node_response in node_responses:
            node_type = node_response.get("node_type", "unknown")
            node_execution_counts[node_type] = node_execution_counts.get(node_type, 0) + 1
    
    # Calculate average response time
    total_exchanges = len(conversation_context)
    average_response_time = total_execution_time / total_exchanges if total_exchanges > 0 else 0.0
    
    # Determine session completion status
    # Default, could be enhanced based on error patterns
    session_completion_status = "completed"  
    
    return {
        "total_execution_time_seconds": total_execution_time,
        "parameter_changes_count": parameter_changes_count,
        "pv_curves_generated_count": pv_curves_generated_count,
        "error_count": error_count,
        "error_types": error_types,
        "node_execution_counts": node_execution_counts,
        "average_response_time_seconds": average_response_time,
        "session_completion_status": session_completion_status
    }

def create_and_save_session(state: dict, provider: str, model_name: str, session_start_time: datetime, session_id: str = None):
    """
    Create a ChatSession from the current state and save it to history.
    
    Args:
        state: Current conversation state
        provider: LLM provider used (ollama/openai)
        model_name: Name of the LLM model used
        session_start_time: When the session started
        session_id: Unique session ID (if None, will generate one)
    """
    try:
        # Use provided session_id or generate a timestamp-based one
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract errors from conversation context
        errors = []
        if state.get("conversation_context"):
            for exchange in state["conversation_context"]:
                if exchange.get("error_info"):
                    errors.append(exchange["error_info"])
        
        # Extract all results from conversation context
        all_results = []
        if state.get("conversation_context"):
            for exchange in state["conversation_context"]:
                if exchange.get("results"):
                    all_results.append(exchange["results"])
        
        # Calculate session metadata
        metadata = calculate_session_metadata(state, session_start_time)
        
        # Create ChatSession
        session = ChatSession(
            session_id=session_id,
            start_time=session_start_time,
            end_time=datetime.now(),
            provider=provider,
            model_name=model_name,
            exchanges=state.get("conversation_context", []),
            total_exchanges=len(state.get("conversation_context", [])),
            errors=errors,
            final_inputs=state.get("inputs", {}).model_dump() if hasattr(state.get("inputs"), 'model_dump') else state.get("inputs", {}),
            all_results=all_results,
            # Include all metadata fields
            **metadata  
        )
        
        # Save the session
        filepath = save_session(session.model_dump(), session_id)
        print(f"Chat session saved: {filepath}")
        
    except Exception as e:
        print(f"Failed to save chat session: {e}")

def list_saved_sessions() -> list:
    """
    List all saved chat sessions from individual JSON files.
    
    Returns:
        list: List of session information dictionaries
    """
    try:
        history_folder = ensure_history_folder()
        
        # Find all chat session files
        session_files = []
        for filename in os.listdir(history_folder):
            if filename.startswith("chat_session_") and filename.endswith(".json"):
                session_files.append(filename)
        
        # Sort by filename (which includes timestamp)
        session_files.sort(reverse=True)  # Most recent first
        
        # Extract session information from each file
        sessions = []
        for filename in session_files:
            try:
                filepath = os.path.join(history_folder, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                sessions.append({
                    "session_id": session_data.get("session_id", "unknown"),
                    "session_name": session_data.get("session_name", "Unknown Session"),
                    "created_at": session_data.get("created_at", "unknown"),
                    "last_updated": session_data.get("last_updated", "unknown"),
                    "total_messages": session_data.get("metadata", {}).get("total_messages", 0),
                    "filename": filename
                })
            except Exception as e:
                print(f"Error reading session file {filename}: {e}")
                continue
        
        return sessions
        
    except Exception as e:
        print(f"Error listing sessions: {e}")
        return []

def load_session(session_id: str) -> Dict[str, Any]:
    """
    Load a chat session from individual JSON files.
    
    Args:
        session_id: ID of the session to load
        
    Returns:
        Dict[str, Any]: Loaded session data
        
    Raises:
        Exception: If there's an error loading the file
    """
    try:
        history_folder = ensure_history_folder()
        
        # Find the session file by scanning all files
        session_file = None
        for filename in os.listdir(history_folder):
            if filename.startswith("chat_session_") and filename.endswith(".json"):
                if session_id in filename:  # Check if session_id is in filename
                    session_file = filename
                    break
        
        if not session_file:
            raise Exception(f"Session file for {session_id} not found")
        
        filepath = os.path.join(history_folder, session_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Verify the session_id matches
        if session_data.get("session_id") != session_id:
            raise Exception(f"Session ID mismatch in file {session_file}")
        
        return session_data
        
    except Exception as e:
        raise Exception(f"Failed to load session {session_id}: {str(e)}")

def get_session_info(session_id: str) -> Dict[str, Any]:
    """
    Get basic information about a session without loading the full data.
    
    Args:
        session_id: ID of the session
        
    Returns:
        Dict[str, Any]: Basic session information
    """
    try:
        history_folder = ensure_history_folder()
        
        # Find the session file by scanning all files
        session_file = None
        for filename in os.listdir(history_folder):
            if filename.startswith("chat_session_") and filename.endswith(".json"):
                if session_id in filename:  # Check if session_id is in filename
                    session_file = filename
                    break
        
        if not session_file:
            return {"error": f"Session file for {session_id} not found"}
        
        filepath = os.path.join(history_folder, session_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Verify the session_id matches
        if session_data.get("session_id") != session_id:
            return {"error": f"Session ID mismatch in file {session_file}"}
        
        return {
            "session_id": session_data.get("session_id", "unknown"),
            "session_name": session_data.get("session_name", "Unknown Session"),
            "created_at": session_data.get("created_at", "unknown"),
            "last_updated": session_data.get("last_updated", "unknown"),
            "total_messages": session_data.get("metadata", {}).get("total_messages", 0),
            "total_cached_results": session_data.get("metadata", {}).get("total_cached_results", 0),
            "filename": session_file
        }
        
    except Exception as e:
        return {"error": str(e)}
