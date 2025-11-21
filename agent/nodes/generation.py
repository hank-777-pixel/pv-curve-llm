from langchain_core.messages import AIMessage
from agent.state.app_state import State
from agent.schemas.response import NodeResponse
from agent.utils.context import get_conversation_context
from agent.utils.display import display_executing_node, console
from datetime import datetime

def generation_agent(state: State, llm, prompts, retriever, generate_pv_curve):
    
    display_executing_node("generation")
    
    inputs = state["inputs"]
    
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
    
    generation_content = (
        f"PV curve generated for {inputs.grid.upper()} system (Bus {inputs.bus_id})\n"
        f"Load type: {load_type}, Power factor: {inputs.power_factor}\n"
        f"Plot saved to {results['save_path']}"
    )
    
    analysis_query = (
        f"PV curve voltage stability analysis nose point load margin "
        f"voltage drop {inputs.grid} power system stability assessment "
        f"power factor {inputs.power_factor} voltage collapse"
    )
    
    context = retriever.invoke(analysis_query)
    
    recent_exchanges = get_conversation_context(state, max_exchanges=3)
    comparison_context = ""
    
    if recent_exchanges:
        comparison_context = "\n\n**Previous Analysis Results for Comparison:**\n"
        
        for i, exchange in enumerate(recent_exchanges, 1):
            if exchange.get('results'):
                prev_results = exchange['results']
                prev_inputs = exchange.get('inputs_state', {})
                comparison_context += f"\n**Previous Analysis {i}:**\n"
                comparison_context += f"- Grid: {prev_results.get('grid_system', 'N/A')}\n"
                comparison_context += f"- Bus: {prev_results.get('bus_monitored', 'N/A')}\n"
                comparison_context += f"- Load Margin: {prev_results.get('load_margin_mw', 'N/A')} MW\n"
                comparison_context += f"- Nose Point Voltage: {prev_results.get('nose_point_voltage_pu', 'N/A')} pu\n"
                comparison_context += f"- Power Factor: {prev_inputs.get('power_factor', 'N/A')}\n"
                comparison_context += f"- Load Type: {'Capacitive' if prev_inputs.get('capacitive', False) else 'Inductive'}\n"
                comparison_context += f"- Converged Steps: {prev_results.get('convergence_steps', 'N/A')}\n"

    console.print(f"[grey50]→ Analyzing results and generating summary...")
    system_prompt = prompts["analysis_agent"]["system"].format(context=context) + comparison_context
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompts["analysis_agent"]["user"].format(
            results=results,
            grid_system=results['grid_system'].upper()
        )}
    ]
    analysis_reply = llm.invoke(messages)
    
    combined_content = f"{generation_content}\n\n{analysis_reply.content}"
    reply = AIMessage(content=combined_content)
    
    node_response = NodeResponse(
        node_type="generation",
        success=True,
        data={
            "pv_results": results,
            "grid_system": inputs.grid,
            "bus_monitored": inputs.bus_id,
            "load_margin_mw": results.get("load_margin_mw"),
            "nose_point_voltage_pu": results.get("nose_point", {}).get("voltage_pu"),
            "analysis": analysis_reply.content,
            "comparison_context_used": bool(comparison_context),
            "exchanges_included": len(recent_exchanges)
        },
        message=combined_content,
        timestamp=datetime.now(),
        metadata={
            "plot_path": results["save_path"],
            "convergence_steps": results["converged_steps"]
        }
    )
    return {"messages": [reply], "results": results, "node_response": node_response}

