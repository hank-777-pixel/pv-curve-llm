from agent.models.state_models import State
from agent.models.plan_models import MessageClassifier, QuestionClassifier, CompoundMessageClassifier, HistoryReferenceClassifier
from agent.models.response_models import NodeResponse
from agent.terminal_ui import info
from datetime import datetime

def classify_message(state: State, llm, prompts):
    info("Classifying response...")
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)
    
    result = classifier_llm.invoke([
        {"role": "system", "content": prompts["classifier"]["system"]},
        {"role": "user", "content": last_message.content}
    ])
    
    node_response = NodeResponse(
        node_type="classifier",
        success=True,
        data={"message_type": result.message_type},
        message=f"Classified as: {result.message_type}",
        timestamp=datetime.now()
    )
    return {"message_type": result.message_type, "node_response": node_response}

def classify_compound_message(state: State, llm, prompts):
    info("Analyzing message...")
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(CompoundMessageClassifier)
    
    result = classifier_llm.invoke([
        {"role": "system", "content": prompts["compound_classifier"]["system"]},
        {"role": "user", "content": last_message.content}
    ])
    
    is_compound = result.message_type == "compound"
    node_response = NodeResponse(
        node_type="compound_classifier",
        success=True,
        data={"is_compound": is_compound, "message_type": result.message_type},
        message=f"Message type: {result.message_type}",
        timestamp=datetime.now()
    )
    return {"is_compound": is_compound, "node_response": node_response}

def question_classifier(state: State, llm, prompts):
    info("Analyzing question...")
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(QuestionClassifier)
    
    result = classifier_llm.invoke([
        {"role": "system", "content": prompts["question_classifier"]["system"]},
        {"role": "user", "content": last_message.content}
    ])
    
    node_response = NodeResponse(
        node_type="question_classifier",
        success=True,
        data={"question_type": result.question_type},
        message=f"Question classified as: {result.question_type}",
        timestamp=datetime.now()
    )
    return {"message_type": result.question_type, "node_response": node_response}

def router(state: State):
    message_type = state.get("message_type", "question")
    
    next_node = "question"
    if message_type == "parameter":
        next_node = "parameter"
    elif message_type == "generation":
        next_node = "generation"
    
    node_response = NodeResponse(
        node_type="router",
        success=True,
        data={"next": next_node, "message_type": message_type},
        message=f"Routing to: {next_node}",
        timestamp=datetime.now()
    )
    return {"next": next_node, "node_response": node_response}

def enhanced_router(state: State):
    if state.get("is_compound"):
        next_node = "planner"
    else:
        message_type = state.get("message_type", "question")
        if message_type == "parameter":
            next_node = "parameter"
        elif message_type == "generation":
            next_node = "generation"
        else:
            next_node = "question"
    
    node_response = NodeResponse(
        node_type="enhanced_router",
        success=True,
        data={"next": next_node, "is_compound": state.get("is_compound", False)},
        message=f"Enhanced routing to: {next_node}",
        timestamp=datetime.now()
    )
    return {"next": next_node, "node_response": node_response}


def detect_history_reference(state: State, llm, prompts):
    """
    Detect if the user is referencing previous conversation context.
    
    This function analyzes the current user message to determine if they are
    referencing past conversation, results, or context. If history reference
    is detected, it sets needs_history=True and provides context window size.
    
    Args:
        state: Current state containing messages and conversation context
        llm: Language model for structured output
        prompts: Dictionary containing system prompts
        
    Returns:
        dict: Contains needs_history flag, confidence, patterns, and context window
    """
    info("Detecting history references...")
    
    # Get the last user message
    last_message = state["messages"][-1]
    user_input = last_message.content.lower()
    
    # Create structured output classifier
    history_classifier_llm = llm.with_structured_output(HistoryReferenceClassifier)
    
    # Prepare the prompt with user input
    result = history_classifier_llm.invoke([
        {"role": "system", "content": prompts["history_detection"]["system"]},
        {"role": "user", "content": last_message.content}
    ])
    
    # Create node response for tracking
    node_response = NodeResponse(
        node_type="history_detection",
        success=True,
        data={
            "needs_history": result.needs_history,
            "confidence": result.confidence,
            "detected_patterns": result.detected_patterns,
            "context_window_size": result.context_window_size
        },
        message=f"History detection: {result.needs_history} (confidence: {result.confidence:.2f})",
        timestamp=datetime.now()
    )
    
    # Return the detection results
    return {
        "needs_history": result.needs_history,
        "confidence": result.confidence,
        "detected_patterns": result.detected_patterns,
        "context_window_size": result.context_window_size,
        "node_response": node_response
    }


def get_relevant_context(state: State, context_window_size: int = 3):
    """
    Extract relevant conversation context based on window size.
    
    This function retrieves the last N exchanges from conversation_context
    to provide relevant historical context when needs_history=True.
    
    Args:
        state: Current state containing conversation_context
        context_window_size: Number of previous exchanges to include
        
    Returns:
        list: List of relevant conversation exchanges
    """
    conversation_context = state.get("conversation_context", [])
    
    # Get the last N exchanges
    if conversation_context:
        relevant_context = conversation_context[-context_window_size:]
    else:
        relevant_context = []
    
    info(f"Retrieved {len(relevant_context)} exchanges from conversation history")
    
    return relevant_context 