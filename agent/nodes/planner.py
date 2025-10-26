from agent.state.app_state import State
from agent.schemas.planner import MultiStepPlan
from agent.schemas.response import NodeResponse
from datetime import datetime

def planner_agent(state: State, llm, prompts):
    last_message = state["messages"][-1]
    planner_llm = llm.with_structured_output(MultiStepPlan)
    
    result = planner_llm.invoke([
        {"role": "system", "content": prompts["planner"]["system"]},
        {"role": "user", "content": prompts["planner"]["user"].format(user_input=last_message.content)}
    ])

    node_response = NodeResponse(
        node_type="planner",
        success=True,
        data={
            "plan_description": result.description,
            "steps_count": len(result.steps),
            "plan": result.model_dump()
        },
        message=f"Plan created with {len(result.steps)} steps: {result.description}",
        timestamp=datetime.now()
    )
    return {"plan": result, "current_step": 0, "step_results": [], "node_response": node_response}

