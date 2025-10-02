from langchain_core.messages import AIMessage
from agent.models.state_models import State
from agent.models.response_models import NodeResponse
from agent.terminal_ui import info, answer
from datetime import datetime

def question_general_agent(state: State, llm, prompts, retriever):
    last_message = state["messages"][-1]
    info("Retrieving context...")
    context = retriever.invoke(last_message.content)
    
    conversation_context = ""
    if state.get("conversation_history"):
        recent_conversations = state["conversation_history"][-3:]
        conversation_context = "\n\nRecent conversation context:\n" + "\n".join([
            f"Previous Q: {conv['user_input']}\nPrevious A: {conv['assistant_response'][:200]}..."
            for conv in recent_conversations
        ])
    
    results_context = ""
    if state.get("cached_results"):
        recent_results = state["cached_results"][-2:]
        results_context = "\n\nPrevious PV curve results for comparison:\n" + "\n".join([
            f"Grid: {res['inputs']['grid']}, Bus: {res['inputs']['bus_id']}, PF: {res['inputs']['power_factor']}"
            for res in recent_results
        ])
    
    info("Analyzing question...")
    system_prompt = prompts["question_general_agent"]["system"].format(context=context) + conversation_context + results_context
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompts["question_general_agent"]["user"].format(user_input=last_message.content)}
    ]
    reply = llm.invoke(messages)
    answer(reply.content)
    node_response = NodeResponse(
        node_type="question_general",
        success=True,
        data={
            "response": reply.content,
            "context_retrieved": len(context),
            "conversation_context": bool(state.get("conversation_history")),
            "results_context": bool(state.get("cached_results"))
        },
        message=reply.content,
        timestamp=datetime.now()
    )
    return {"messages": [reply], "node_response": node_response}

def question_parameter_agent(state: State, llm, prompts):
    last_message = state["messages"][-1]
    info("Explaining parameters...")
    messages = [
        {"role": "system", "content": prompts["question_parameter_agent"]["system"]},
        {"role": "user", "content": last_message.content}
    ]
    reply = llm.invoke(messages)
    answer(reply.content)
    node_response = NodeResponse(
        node_type="question_parameter",
        success=True,
        data={"response": reply.content},
        message=reply.content,
        timestamp=datetime.now()
    )
    return {"messages": [reply], "node_response": node_response}

def generation_agent(state: State, generate_pv_curve):
    info("Generating PV curve...")
    from langchain_core.messages import AIMessage
    inputs = state["inputs"]
    
    try:
        results = generate_pv_curve(
            grid=inputs.grid,
            target_bus_idx=inputs.bus_id,
            step_size=inputs.step_size,
            max_scale=inputs.max_scale,
            power_factor=inputs.power_factor,
            voltage_limit=inputs.voltage_limit,
            capacitive=inputs.capacitive,
        )
        
        load_type = "capacitive" if inputs.capacitive else "inductive"
        
        reply_content = (
            f"PV curve generated for {inputs.grid.upper()} system (Bus {inputs.bus_id})\n"
            f"Load type: {load_type}, Power factor: {inputs.power_factor}\n"
            f"Plot saved to {results['save_path']}"
        )
        
        # Show positive generation success message
        load_type_display = "Capacitive" if inputs.capacitive else "Inductive"
        info(f"PV Curve Generated: {inputs.grid.upper()} Bus {inputs.bus_id} | Step: {inputs.step_size} | Max Scale: {inputs.max_scale} | PF: {inputs.power_factor} | V Limit: {inputs.voltage_limit} | Load: {load_type_display}")
        
        reply = AIMessage(content=reply_content)
        node_response = NodeResponse(
            node_type="generation",
            success=True,
            data={
                "pv_results": results,
                "grid_system": inputs.grid,
                "bus_monitored": inputs.bus_id,
                "load_margin_mw": results.get("load_margin_mw"),
                "nose_point_voltage_pu": results.get("nose_point", {}).get("voltage_pu")
            },
            message=reply_content,
            timestamp=datetime.now(),
            metadata={
                "plot_path": results["save_path"],
                "convergence_steps": results["converged_steps"]
            }
        )
        return {"messages": [reply], "results": results, "node_response": node_response}
    
    except Exception as e:
        info(f"Generation failed: {str(e)}")
        node_response = NodeResponse(
            node_type="generation",
            success=False,
            data={"error": str(e)},
            message=f"Failed to generate PV curve: {str(e)}",
            timestamp=datetime.now()
        )
        return {"error_info": {
            "error_type": "simulation_error",
            "error_message": str(e),
            "current_inputs": inputs.model_dump(),
            "context": "PV curve simulation failed"
        }, "failed_node": "generation", "node_response": node_response}

def analysis_agent(state: State, llm, prompts, retriever):
    info("Analyzing PV curve results...")
    results = state.get("results")
    if not results:
        reply = AIMessage(content="No PV curve results available for analysis.")
        node_response = NodeResponse(
            node_type="analysis",
            success=True,
            data={"response": "No PV curve results available for analysis."},
            message="No PV curve results available for analysis.",
            timestamp=datetime.now()
        )
        return {"messages": [reply], "node_response": node_response}
    
    inputs = state["inputs"]
    analysis_query = (
        f"PV curve voltage stability analysis nose point load margin "
        f"voltage drop {inputs.grid} power system stability assessment "
        f"power factor {inputs.power_factor} voltage collapse"
    )
    
    info("Retrieving analysis context...")
    context = retriever.invoke(analysis_query)
    
    comparison_context = ""
    if state.get("cached_results") and len(state["cached_results"]) > 1:
        prev_results = state["cached_results"][-2:-1]
        if prev_results:
            prev = prev_results[0]["results"]
            comparison_context = f"\n\nPrevious curve for comparison: Grid {prev['grid_system']}, Bus {prev['bus_monitored']}, Load margin: {prev.get('load_margin_mw', 'N/A')} MW, Nose voltage: {prev.get('nose_point_voltage_pu', 'N/A')} pu"
    
    info("Performing analysis...")
    system_prompt = prompts["analysis_agent"]["system"].format(context=context) + comparison_context
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompts["analysis_agent"]["user"].format(
            results=results,
            grid_system=results['grid_system'].upper()
        )}
    ]
    reply = llm.invoke(messages)
    
    info("Analysis completed")
    answer(reply.content)
    
    node_response = NodeResponse(
        node_type="analysis",
        success=True,
        data={
            "analysis": reply.content,
            "results_analyzed": results
        },
        message=reply.content,
        timestamp=datetime.now()
    )
    return {"messages": [reply], "node_response": node_response}

def error_handler_agent(state: State, llm, prompts):
    info("Handling error...")
    error_info = state.get("error_info", {})
    retry_count = state.get("retry_count", 0)
    failed_node = state.get("failed_node")
    
    if retry_count < 2 and error_info.get("error_type") in ["simulation_error", "validation_error"]:
        info(f"Attempting retry {retry_count + 1}/2...")
        
        if error_info.get("error_type") == "simulation_error":
            current_inputs = state["inputs"]
            corrected_inputs = current_inputs.model_copy()
            
            error_msg = error_info.get("error_message", "").lower()
            if "unsupported grid" in error_msg or "grid" in error_msg:
                if "39" in error_msg:
                    corrected_inputs = corrected_inputs.model_copy(update={"grid": "ieee39"})
                elif "14" in error_msg:
                    corrected_inputs = corrected_inputs.model_copy(update={"grid": "ieee14"})
                elif "118" in error_msg:
                    corrected_inputs = corrected_inputs.model_copy(update={"grid": "ieee118"})
            
            if "bus" in error_msg and "out of range" in error_msg:
                corrected_inputs = corrected_inputs.model_copy(update={"bus_id": 0})
            
            info(f"Corrected parameters, retrying {failed_node}...")
            return {
                "inputs": corrected_inputs,
                "retry_count": retry_count + 1,
                "error_info": None,
                "retry_node": failed_node
            }
    
    error_context = f"""
Error Type: {error_info.get('error_type', 'unknown')}
Error Message: {error_info.get('error_message', 'No message available')}
Context: {error_info.get('context', 'No context available')}

Current Inputs: {error_info.get('current_inputs', 'Not available')}
User Input: {error_info.get('user_input', 'Not available')}
Additional Info: {error_info.get('validation_errors', 'None')}
"""
    
    messages = [
        {"role": "system", "content": prompts["error_handler"]["system"]},
        {"role": "user", "content": prompts["error_handler_user"]["user"].format(error_context=error_context)}
    ]
    
    reply = llm.invoke(messages)
    info(f"Error handled: {error_info.get('error_type', 'unknown')}")
    
    node_response = NodeResponse(
        node_type="error_handler",
        success=True,
        data={"error_resolved": True, "error_type": error_info.get('error_type', 'unknown')},
        message=reply.content,
        timestamp=datetime.now()
    )
    return {"messages": [reply], "retry_count": 0, "failed_node": None, "node_response": node_response}

def compound_summary_agent(state: State):
    info("Summarizing multi-step results...")
    plan = state.get("plan")
    step_results = state.get("step_results", [])
    
    summary_parts = [f"Completed multi-step request: {plan.description if plan else 'Unknown'}\n"]
    
    for i, result in enumerate(step_results):
        step_info = plan.steps[i] if plan and i < len(plan.steps) else None
        action_name = step_info.action if step_info else result.get("action", "unknown")
        result_text = result['result'][:100] + "..." if len(result['result']) > 100 else result['result']
        summary_parts.append(f"Step {i+1} ({action_name}): {result_text}")
    
    summary = "\n".join(summary_parts)
    reply = AIMessage(content=summary)
    
    info("Multi-step plan completed")
    
    node_response = NodeResponse(
        node_type="compound_summary",
        success=True,
        data={
            "summary": summary,
            "steps_completed": len(step_results),
            "plan_description": plan.description if plan else "Unknown"
        },
        message=summary,
        timestamp=datetime.now()
    )
    return {"messages": [reply], "node_response": node_response} 