from langchain_core.messages import AIMessage
from pydantic import ValidationError
from agent.models.state_models import State
from agent.models.plan_models import InputModifier, MultiStepPlan
from agent.terminal_ui import info, answer

def parameter_agent(state: State, llm, prompts):
    info("Processing parameter changes...")
    last_message = state["messages"][-1]
    modifier_llm = llm.with_structured_output(InputModifier)
    current_inputs = state["inputs"]
    
    try:
        result = modifier_llm.invoke([
            {"role": "system", "content": prompts["parameter_agent"]["system"].format(current_inputs=current_inputs)},
            {"role": "user", "content": last_message.content}
        ])
    except Exception as e:
        return {"error_info": {
            "error_type": "parameter_parsing",
            "error_message": str(e),
            "user_input": last_message.content,
            "current_inputs": current_inputs.model_dump(),
            "context": "Failed to parse parameter modification request"
        }, "failed_node": "parameter"}
    
    try:
        updates = {}
        reply_parts = []
        
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
            reply_parts.append(f"{modification.parameter} to {converted_value}")
        
        new_inputs = current_inputs.model_copy(update=updates)
        
        if len(reply_parts) == 1:
            reply_content = f"Updated {reply_parts[0]}"
        else:
            reply_content = f"Updated {len(reply_parts)} parameters:\n" + "\n".join(f"• {part}" for part in reply_parts)
        
        # Show the parameter changes immediately
        answer(reply_content)
        
        reply = AIMessage(content=reply_content)
        return {"messages": [reply], "inputs": new_inputs}
        
    except ValidationError as e:
        error_details = [f"{error.get('loc', ['unknown'])[0]}: {error.get('msg', 'Invalid value')}" for error in e.errors()]
        return {"error_info": {
            "error_type": "validation_error",
            "error_message": '; '.join(error_details),
            "user_input": last_message.content,
            "current_inputs": current_inputs.model_dump(),
            "context": "Parameter validation failed",
            "validation_errors": e.errors()
        }, "failed_node": "parameter"}
    except ValueError as e:
        return {"error_info": {
            "error_type": "type_conversion",
            "error_message": str(e),
            "user_input": last_message.content,
            "current_inputs": current_inputs.model_dump(),
            "context": "Failed to convert parameter value to correct type"
        }, "failed_node": "parameter"}

def planner_agent(state: State, llm, prompts):
    info("Creating multi-step plan...")
    last_message = state["messages"][-1]
    planner_llm = llm.with_structured_output(MultiStepPlan)
    
    result = planner_llm.invoke([
        {"role": "system", "content": prompts["planner"]["system"]},
        {"role": "user", "content": prompts["planner"]["user"].format(user_input=last_message.content)}
    ])
    
    info(f"Plan created with {len(result.steps)} steps: {result.description}")
    
    # List out all planned steps
    info("\nPlanned steps:")
    for i, step in enumerate(result.steps, 1):
        step_desc = f"Step {i}: {step.action}"
        if step.parameters:
            param_dict = step.parameters.model_dump(exclude_none=True)
            param_desc = ", ".join([f"{k}={v}" for k, v in param_dict.items()])
            step_desc += f" ({param_desc})"
        if step.content and step.content != step.action:
            step_desc += f" - {step.content}"
        info(f"  {step_desc}")
    
    
    return {"plan": result, "current_step": 0, "step_results": []}

def step_controller(state: State):
    plan = state.get("plan")
    current_step = state.get("current_step", 0)
    
    if not plan or current_step >= len(plan.steps):
        return {"next": "compound_summary"}
    
    step = plan.steps[current_step]
    info(f"Executing step {current_step + 1} of {len(plan.steps)}: {step.action}")
    
    if step.action == "parameter" and step.parameters:
        try:
            current_inputs = state["inputs"]
            updates = {}
            reply_parts = []
            
            param_dict = step.parameters.model_dump(exclude_none=True)
            for param, value in param_dict.items():
                converted_value = value
                if param == "grid":
                    # Normalize grid system names
                    value_str = str(value).lower().replace(" ", "").replace("_", "")
                    if "14" in value_str:
                        converted_value = "ieee14"
                    elif "24" in value_str:
                        converted_value = "ieee24"
                    elif "30" in value_str:
                        converted_value = "ieee30"
                    elif "39" in value_str:
                        converted_value = "ieee39"
                    elif "57" in value_str:
                        converted_value = "ieee57"
                    elif "118" in value_str:
                        converted_value = "ieee118"
                    elif "300" in value_str:
                        converted_value = "ieee300"
                    else:
                        converted_value = value  # Keep original if no match
                elif param in ["bus_id"]:
                    converted_value = int(value)
                elif param in ["step_size", "max_scale", "power_factor", "voltage_limit"]:
                    converted_value = float(value)
                elif param in ["capacitive", "continuation"]:
                    if isinstance(value, str):
                        converted_value = value.lower() in ["true", "yes", "1", "on"]
                    else:
                        converted_value = bool(value)
                
                updates[param] = converted_value
                reply_parts.append(f"{param} to {converted_value}")
            
            new_inputs = current_inputs.model_copy(update=updates)
            
            if len(reply_parts) == 1:
                reply_content = f"Updated {reply_parts[0]}"
            else:
                reply_content = f"Updated {len(reply_parts)} parameters:\n" + "\n".join(f"• {part}" for part in reply_parts)
            
            answer(reply_content)
            
            reply = AIMessage(content=reply_content)
            return {"messages": [reply], "inputs": new_inputs, "next": "advance_step"}
            
        except Exception as e:
            return {"error_info": {
                "error_type": "parameter_processing",
                "error_message": str(e),
                "user_input": step.content,
                "current_inputs": state["inputs"].model_dump(),
                "context": "Failed to process planned parameter modification"
            }, "next": "error_handler"}
    
    from langchain_core.messages import HumanMessage
    step_message = HumanMessage(content=step.content)
    return {"messages": [step_message], "message_type": step.action, "next": step.action}

def advance_step(state: State):
    current_step = state.get("current_step", 0)
    plan = state.get("plan")
    step_results = state.get("step_results", [])
    
    if state.get("messages"):
        last_message = state["messages"][-1]
        result_preview = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        current_step_action = plan.steps[current_step].action if plan and current_step < len(plan.steps) else "unknown"
        
        step_results.append({
            "step": current_step,
            "action": current_step_action,
            "result": last_message.content if hasattr(last_message, 'content') else str(last_message)
        })
    
    next_step = current_step + 1
    
    return {
        "current_step": next_step,
        "step_results": step_results,
        "next": "step_controller" if plan and next_step < len(plan.steps) else "compound_summary"
    } 