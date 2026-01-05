from langchain_core.messages import AIMessage
from agent.state.app_state import State
from agent.schemas.response import NodeResponse
from agent.schemas.parameter import InputModifier
from agent.utils.display import display_executing_node, console
from datetime import datetime
import json

def generation_agent(state: State, llm, prompts, retriever, generate_pv_curve):
    display_executing_node("generation")
    
    inputs = state["inputs"]
    last_message = state["messages"][-1]
    
    # Extract parameters from user's message if they're present
    # This allows "generate pv curve that power factor is 0.9" to work
    modifier_llm = llm.with_structured_output(InputModifier)
    result = modifier_llm.invoke([
        {"role": "system", "content": prompts["parameter_agent"]["system"].format(current_inputs=inputs)},
        {"role": "user", "content": last_message.content}
    ])
    
    # Update inputs if parameters were found in the message
    if result.modifications:
        updates = {}
        for modification in result.modifications:
            converted_value = modification.value
            if modification.parameter in ["bus_id"]:
                converted_value = int(modification.value)
            elif modification.parameter in ["step_size", "max_scale", "power_factor", "voltage_limit"]:
                converted_value = float(modification.value)
            elif modification.parameter in ["capacitive", "continuation"]:
                if isinstance(modification.value, str):
                    converted_value = modification.value.lower() in ["true", "yes", "1", "on"]
                else:
                    converted_value = bool(modification.value)
            
            updates[modification.parameter] = converted_value
        
        # Update inputs with extracted parameters
        inputs = inputs.model_copy(update=updates)
    
<<<<<<< HEAD
=======
    # Generate PV curve with plot (skip_plot=False by default)
>>>>>>> 848daa2 (seperate generate curve and analysis into two seperate node)
    results = generate_pv_curve(
        grid=inputs.grid,
        target_bus_idx=inputs.bus_id,
        step_size=inputs.step_size,
        max_scale=inputs.max_scale,
        power_factor=inputs.power_factor,
        voltage_limit=inputs.voltage_limit,
        capacitive=inputs.capacitive,
        skip_plot=False,  # Generate the visual graph
    )
    
    load_type = "capacitive" if inputs.capacitive else "inductive"
    
    generation_content = (
        f"PV curve generated for {inputs.grid.upper()} system (Bus {inputs.bus_id})\n"
        f"Load type: {load_type}, Power factor: {inputs.power_factor}\n"
        f"Plot saved to {results['save_path']}"
    )
    
<<<<<<< HEAD
    analysis_query = (
        f"PV curve voltage stability analysis nose point load margin "
        f"voltage drop {inputs.grid} power system stability assessment "
        f"power factor {inputs.power_factor} voltage collapse"
    )
    
    context = retriever.invoke(analysis_query)
    
    recent_exchanges = get_conversation_context(state, max_exchanges=5)
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

    # Reduce data sent to LLM by sampling curve_points strategically
    # This prevents issues from huge prompts while preserving key information
    curve_points = results.get('curve_points', [])
    nose_point_idx = results.get('nose_point', {}).get('index', 0)
    
    # Sample curve_points: first 5, every 10th in middle, ±5 around nose, last 5
    sampled_indices = set()
    
    # First 5 points (initial region)
    sampled_indices.update(range(min(5, len(curve_points))))
    
    # Every 10th point in middle region (skip first/last 5)
    for i in range(5, len(curve_points) - 5, 10):
        sampled_indices.add(i)
    
    # Points around nose point (±5 points)
    nose_start = max(0, nose_point_idx - 5)
    nose_end = min(len(curve_points), nose_point_idx + 6)
    sampled_indices.update(range(nose_start, nose_end))
    
    # Last 5 points (final region)
    sampled_indices.update(range(max(0, len(curve_points) - 5), len(curve_points)))
    
    # Sort indices and create sampled curve_points
    sampled_indices = sorted(sampled_indices)
    sampled_curve_points = [curve_points[i] for i in sampled_indices if i < len(curve_points)]
    
    # Create reduced results dict with sampled curve_points
    # Keep all summary statistics but use sampled curve_points
    reduced_results = results.copy()
    reduced_results['curve_points'] = sampled_curve_points
    reduced_results['curve_points_sampled'] = True
    reduced_results['total_curve_points'] = len(curve_points)
    reduced_results['sampled_curve_points_count'] = len(sampled_curve_points)
    
    # Also reduce load_values_mw and voltage_values_pu arrays to match sampled points
    # This keeps the data consistent
    if 'load_values_mw' in results and 'voltage_values_pu' in results:
        reduced_results['load_values_mw'] = [results['load_values_mw'][i] for i in sampled_indices if i < len(results['load_values_mw'])]
        reduced_results['voltage_values_pu'] = [results['voltage_values_pu'][i] for i in sampled_indices if i < len(results['voltage_values_pu'])]
    
    # Serialize reduced results to JSON
    results_json = json.dumps(reduced_results, indent=2)
    
    system_prompt = prompts["analysis_agent"]["system"].format(context=context) + comparison_context
    
    user_prompt = prompts["analysis_agent"]["user"].format(
        results=results_json,
        grid_system=results['grid_system'].upper()
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    analysis_reply = llm.invoke(messages)
    
    combined_content = f"{generation_content}\n\n{analysis_reply.content}"
    reply = AIMessage(content=combined_content)
=======
    # No analysis here - just generation
    reply = AIMessage(content=generation_content)
>>>>>>> 848daa2 (seperate generate curve and analysis into two seperate node)
    
    node_response = NodeResponse(
        node_type="generation",
        success=True,
        data={
            "pv_results": results,
            "grid_system": inputs.grid,
            "bus_monitored": inputs.bus_id,
            "load_margin_mw": results.get("load_margin_mw"),
            "nose_point_voltage_pu": results.get("nose_point", {}).get("voltage_pu"),
        },
        message=generation_content,
        timestamp=datetime.now(),
        metadata={
            "plot_path": results["save_path"],
            "convergence_steps": results["converged_steps"]
        }
    )
    # Return updated inputs if they were modified
    return_value = {"messages": [reply], "results": results, "node_response": node_response}
    if result.modifications:
        return_value["inputs"] = inputs
    return return_value

