from langgraph.graph import StateGraph, START, END
from agent.models.state_models import State
from agent.nodes.classifier_nodes import classify_message, question_classifier, router
from agent.nodes.parameter_nodes import parameter_agent
from agent.nodes.execution_nodes import (
    question_general_agent, 
    question_parameter_agent, 
    generation_agent, 
    analysis_agent, 
    error_handler_agent
)

def create_simple_workflow(llm, prompts, retriever, generate_pv_curve):
    graph_builder = StateGraph(State)
    
    # Add nodes with dependencies injected
    graph_builder.add_node("classifier", lambda state: classify_message(state, llm, prompts))
    graph_builder.add_node("router", router)
    graph_builder.add_node("question", lambda state: question_classifier(state, llm, prompts))
    graph_builder.add_node("question_general", lambda state: question_general_agent(state, llm, prompts, retriever))
    graph_builder.add_node("question_parameter", lambda state: question_parameter_agent(state, llm, prompts))
    graph_builder.add_node("parameter", lambda state: parameter_agent(state, llm, prompts))
    graph_builder.add_node("generation", lambda state: generation_agent(state, generate_pv_curve))
    graph_builder.add_node("analysis", lambda state: analysis_agent(state, llm, prompts, retriever))
    graph_builder.add_node("error_handler", lambda state: error_handler_agent(state, llm, prompts))
    
    # Define edges
    graph_builder.add_edge(START, "classifier")
    graph_builder.add_edge("classifier", "router")
    
    graph_builder.add_conditional_edges(
        "router",
        lambda state: state.get("next"),
        {
            "question": "question",
            "parameter": "parameter",
            "generation": "generation"
        }
    )
    
    graph_builder.add_conditional_edges(
        "question",
        lambda state: state.get("message_type"),
        {
            "question_general": "question_general",
            "question_parameter": "question_parameter"
        }
    )
    
    graph_builder.add_edge("question_general", END)
    graph_builder.add_edge("question_parameter", END)
    graph_builder.add_edge("generation", "analysis")
    graph_builder.add_edge("analysis", END)
    # Error handling with retry
    def route_after_error(state):
        if state.get("retry_node"):
            return state["retry_node"]
        return "END"
    
    graph_builder.add_conditional_edges(
        "error_handler",
        route_after_error,
        {
            "parameter": "parameter",
            "generation": "generation",
            "END": END
        }
    )
    
    graph_builder.add_conditional_edges(
        "parameter",
        lambda state: "error_handler" if state.get("error_info") else "END",
        {
            "error_handler": "error_handler",
            "END": END
        }
    )
    
    graph_builder.add_conditional_edges(
        "generation",
        lambda state: "error_handler" if state.get("error_info") else "analysis",
        {
            "error_handler": "error_handler",
            "analysis": "analysis"
        }
    )
    
    return graph_builder.compile() 