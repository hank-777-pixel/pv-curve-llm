from langchain_core.messages import AIMessage
from agent.models.state_models import State

def question_general_agent(state: State, llm, prompts, retriever):
    print("📚 Retrieving context...")
    last_message = state["messages"][-1]
    context = retriever.invoke(last_message.content)
    
    print("🧠 Analyzing question...")
    messages = [
        {"role": "system", "content": prompts["question_general_agent"]["system"].format(context=context)},
        {"role": "user", "content": prompts["question_general_agent"]["user"].format(user_input=last_message.content)}
    ]
    
    reply = llm.invoke(messages)
    
    # Show a preview of the answer for multi-step plans
    if state.get("is_compound"):
        answer_preview = reply.content[:100] + "..." if len(reply.content) > 100 else reply.content
        print(f"💬 Answer: {answer_preview}")
    
    return {"messages": [reply]}

def question_parameter_agent(state: State, llm, prompts):
    print("📖 Explaining parameters...")
    last_message = state["messages"][-1]
    
    messages = [
        {"role": "system", "content": prompts["question_parameter_agent"]["system"]},
        {"role": "user", "content": last_message.content}
    ]
    
    reply = llm.invoke(messages)
    
    # Show a preview of the explanation for multi-step plans
    if state.get("is_compound"):
        explanation_preview = reply.content[:100] + "..." if len(reply.content) > 100 else reply.content
        print(f"📝 Explanation: {explanation_preview}")
    
    return {"messages": [reply]}

def generation_agent(state: State, generate_pv_curve):
    print("📊 Generating PV curve...")
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
            continuation=inputs.continuation,
        )
        
        load_type = "capacitive" if inputs.capacitive else "inductive"
        curve_type = "with continuation curve" if inputs.continuation else "upper branch only"
        
        reply_content = (
            f"PV curve generated for {inputs.grid.upper()} system (Bus {inputs.bus_id})\n"
            f"Load type: {load_type}, Power factor: {inputs.power_factor}\n"
            f"Plot saved to {results['save_path']} ({curve_type})"
        )
        
        # Show positive generation success message
        print(f"✅ PV Curve Generated: {inputs.grid.upper()} Bus {inputs.bus_id}, PF: {inputs.power_factor}")
        
        reply = AIMessage(content=reply_content)
        return {"messages": [reply], "results": results}
    
    except Exception as e:
        print(f"❌ Generation failed: {str(e)}")
        return {"error_info": {
            "error_type": "simulation_error",
            "error_message": str(e),
            "current_inputs": inputs.model_dump(),
            "context": "PV curve simulation failed"
        }}

def analysis_agent(state: State, llm, prompts, retriever):
    print("📈 Analyzing PV curve results...")
    results = state.get("results")
    if not results:
        reply = AIMessage(content="No PV curve results available for analysis.")
        return {"messages": [reply]}
    
    inputs = state["inputs"]
    analysis_query = (
        f"PV curve voltage stability analysis nose point load margin "
        f"voltage drop {inputs.grid} power system stability assessment "
        f"power factor {inputs.power_factor} voltage collapse"
    )
    
    print("📚 Retrieving analysis context...")
    context = retriever.invoke(analysis_query)
    
    print("🧠 Performing analysis...")
    messages = [
        {"role": "system", "content": prompts["analysis_agent"]["system"].format(context=context)},
        {"role": "user", "content": prompts["analysis_agent"]["user"].format(
            results=results,
            grid_system=results['grid_system'].upper()
        )}
    ]
    
    reply = llm.invoke(messages)
    
    # Show analysis completion
    print("✅ Analysis completed")
    
    return {"messages": [reply]}

def error_handler_agent(state: State, llm, prompts):
    print("⚠️ Handling error...")
    error_info = state.get("error_info", {})
    
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
        {"role": "user", "content": f"Please analyze this error and provide a helpful explanation:\n\n{error_context}"}
    ]
    
    reply = llm.invoke(messages)
    
    # Show error handling completion
    print(f"⚠️ Error handled: {error_info.get('error_type', 'unknown')}")
    
    return {"messages": [reply]}

def compound_summary_agent(state: State):
    print("📝 Summarizing multi-step results...")
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
    
    print("✅ Multi-step plan completed")
    
    return {"messages": [reply]} 