from agent.models.state_models import State
from agent.models.plan_models import MessageClassifier, QuestionClassifier, CompoundMessageClassifier
from agent.terminal_ui import info

def classify_message(state: State, llm, prompts):
    info("Classifying response...")
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)
    
    result = classifier_llm.invoke([
        {"role": "system", "content": prompts["classifier"]["system"]},
        {"role": "user", "content": last_message.content}
    ])
    
    return {"message_type": result.message_type}

def classify_compound_message(state: State, llm, prompts):
    info("Analyzing message...")
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(CompoundMessageClassifier)
    
    result = classifier_llm.invoke([
        {"role": "system", "content": prompts["compound_classifier"]["system"]},
        {"role": "user", "content": last_message.content}
    ])
    
    return {"is_compound": result.message_type == "compound"}

def question_classifier(state: State, llm, prompts):
    info("Analyzing question...")
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(QuestionClassifier)
    
    result = classifier_llm.invoke([
        {"role": "system", "content": prompts["question_classifier"]["system"]},
        {"role": "user", "content": last_message.content}
    ])
    
    return {"message_type": result.question_type}

def router(state: State):
    message_type = state.get("message_type", "question")
    
    if message_type == "parameter":
        return {"next": "parameter"}
    if message_type == "generation":
        return {"next": "generation"}
    
    return {"next": "question"}

def enhanced_router(state: State):
    if state.get("is_compound"):
        return {"next": "planner"}
    
    message_type = state.get("message_type", "question")
    if message_type == "parameter":
        return {"next": "parameter"}
    if message_type == "generation":
        return {"next": "generation"}
    return {"next": "question"} 