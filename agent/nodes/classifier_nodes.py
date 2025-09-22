from agent.models.state_models import State
from agent.models.plan_models import MessageClassifier, QuestionClassifier, CompoundMessageClassifier
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