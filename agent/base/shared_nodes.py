from agent.models.state_models import State

def simple_state_node(state: State):
    """Simple pass-through node for testing or debugging"""
    return state

def log_state_node(state: State, node_name: str = "unknown"):
    """Node that logs current state for debugging"""
    print(f"[{node_name}] Current step: {state.get('current_step', 0)}")
    print(f"[{node_name}] Is compound: {state.get('is_compound', False)}")
    print(f"[{node_name}] Messages count: {len(state.get('messages', []))}")
    return state

def state_validator_node(state: State):
    """Node that validates state integrity"""
    from .common_utils import validate_state
    
    validations = validate_state(state)
    if not all(validations.values()):
        print(f"State validation warnings: {validations}")
    
    return state 