import json
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from agent.schemas.session import ChatSession


def ensure_history_folder():
    current_dir = Path(__file__).parent.parent
    history_folder = current_dir / "history"
    history_folder.mkdir(exist_ok=True)
    return str(history_folder)

def save_session(session_data: Dict[str, Any], session_id: str) -> str:
    history_folder = ensure_history_folder()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"chat_session_{session_id}_{timestamp}.json"
    filepath = os.path.join(history_folder, filename)
    
    session_data_formatted = convert_session_to_new_format(session_data, session_id)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(session_data_formatted, f, indent=2, ensure_ascii=False, default=str)
    
    return filepath



def convert_session_to_new_format(session_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    provider = session_data.get("provider", "unknown")
    model_name = session_data.get("model_name", "unknown")
    start_time = session_data.get("start_time", datetime.now().isoformat())
    end_time = session_data.get("end_time", datetime.now().isoformat())
    session_name = f"PV_Curve_Session_{provider}"
    messages = []
    
    for exchange in session_data.get("exchanges", []):
        messages.append({
            "timestamp": exchange.get("timestamp", datetime.now().isoformat()),
            "user_input": exchange.get("user_input", ""),
            "assistant_response": exchange.get("assistant_response", ""),
            "inputs_used": exchange.get("inputs_state", {})
        })
    
    cached_results = []
    metadata = {
        "total_messages": len(messages),
        "total_cached_results": len(cached_results)
    }
    
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
    assistant_response = ""
    if new_state.get("messages") and len(new_state["messages"]) > 0:
        assistant_response = new_state["messages"][-1].content
    
    exchange_data = {
        "user_input": user_input,
        "assistant_response": assistant_response,
        "timestamp": datetime.now().isoformat(),
        "message_type": new_state.get("message_type"),
        "inputs_state": new_state.get("inputs", {}).model_dump() if hasattr(new_state.get("inputs"), 'model_dump') else new_state.get("inputs", {}),
        "results": new_state.get("results"),
        "error_info": new_state.get("error_info")
    }
    
    conversation_context = new_state.get("conversation_context", [])
    conversation_context.append(exchange_data)
    
    if len(conversation_context) > max_exchanges:
        conversation_context = conversation_context[-max_exchanges:]
    
    return conversation_context

def calculate_session_metadata(state: dict, session_start_time: datetime) -> dict:
    conversation_context = state.get("conversation_context", [])
    end_time = datetime.now()
    total_execution_time = (end_time - session_start_time).total_seconds()
    
    parameter_changes_count = 0
    for exchange in conversation_context:
        if exchange.get("message_type") == "parameter_change":
            parameter_changes_count += 1
    
    pv_curves_generated_count = 0
    for exchange in conversation_context:
        if exchange.get("results") and exchange.get("message_type") in ["analysis", "pv_curve"]:
            pv_curves_generated_count += 1
    
    error_count = 0
    error_types = []
    for exchange in conversation_context:
        if exchange.get("error_info"):
            error_count += 1
            error_type = exchange["error_info"].get("error_type", "unknown")
            if error_type not in error_types:
                error_types.append(error_type)
    
    node_execution_counts = {}
    for exchange in conversation_context:
        node_responses = exchange.get("node_responses", [])
        for node_response in node_responses:
            node_type = node_response.get("node_type", "unknown")
            node_execution_counts[node_type] = node_execution_counts.get(node_type, 0) + 1
    
    total_exchanges = len(conversation_context)
    average_response_time = total_execution_time / total_exchanges if total_exchanges > 0 else 0.0
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
    if session_id is None:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    errors = []
    if state.get("conversation_context"):
        for exchange in state["conversation_context"]:
            if exchange.get("error_info"):
                errors.append(exchange["error_info"])
    
    all_results = []
    if state.get("conversation_context"):
        for exchange in state["conversation_context"]:
            if exchange.get("results"):
                all_results.append(exchange["results"])
    
    metadata = calculate_session_metadata(state, session_start_time)
    
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
        **metadata  
    )
    
    filepath = save_session(session.model_dump(), session_id)
    print(f"Chat session saved: {filepath}")

def list_saved_sessions() -> list:
    history_folder = ensure_history_folder()
    
    session_files = []
    for filename in os.listdir(history_folder):
        if filename.startswith("chat_session_") and filename.endswith(".json"):
            session_files.append(filename)
    
    session_files.sort(reverse=True)
    
    sessions = []
    for filename in session_files:
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
    
    return sessions

def load_session(session_id: str) -> Dict[str, Any]:
    history_folder = ensure_history_folder()
    session_file = None
    for filename in os.listdir(history_folder):
        if filename.startswith("chat_session_") and filename.endswith(".json"):
            if session_id in filename:
                session_file = filename
                break
    
    if not session_file:
        raise Exception(f"Session file for {session_id} not found")
    
    filepath = os.path.join(history_folder, session_file)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    if session_data.get("session_id") != session_id:
        raise Exception(f"Session ID mismatch in file {session_file}")
    
    return session_data

def get_session_info(session_id: str) -> Dict[str, Any]:
    history_folder = ensure_history_folder()
    session_file = None
    for filename in os.listdir(history_folder):
        if filename.startswith("chat_session_") and filename.endswith(".json"):
            if session_id in filename:
                session_file = filename
                break
    
    if not session_file:
        return {"error": f"Session file for {session_id} not found"}
    
    filepath = os.path.join(history_folder, session_file)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
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
