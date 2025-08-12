from typing_extensions import Literal
from typing import Union, List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class MessageClassifier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    message_type: Literal["question", "parameter", "generation"] = Field(
        ...,
        description="Classify if the message requires a parameter modification, a PV-curve generation/run, or a question/request that requires a knowledge response."
    )

class QuestionClassifier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    question_type: Literal["question_general", "question_parameter"] = Field(
        ...,
        description="Classify if the question is a general voltage stability/PV curve question or specifically about parameter meanings/functionality."
    )

class ParameterModification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    parameter: str = Field(..., description="The parameter to modify")
    value: Union[str, float, int, bool] = Field(..., description="The new value for the parameter")

class InputModifier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    modifications: List[ParameterModification] = Field(..., description="List of parameter modifications to apply")

class StepParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    grid: Optional[str] = Field(None, description="Grid system (e.g., ieee14, ieee118)")
    bus_id: Optional[int] = Field(None, description="Bus ID to monitor")
    step_size: Optional[float] = Field(None, description="Load increment step size")
    max_scale: Optional[float] = Field(None, description="Maximum load multiplier")
    power_factor: Optional[float] = Field(None, description="Power factor")
    voltage_limit: Optional[float] = Field(None, description="Voltage threshold")
    capacitive: Optional[bool] = Field(None, description="Load type - true for capacitive")
    continuation: Optional[bool] = Field(None, description="Curve type - true for continuous")

class StepType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    action: Literal["question", "parameter", "generation"] = Field(..., description="The type of action to perform")
    content: str = Field(..., description="The specific content for this step")
    parameters: Optional[StepParameters] = Field(None, description="Parameters for this step if it's a parameter modification")

class MultiStepPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    steps: List[StepType] = Field(..., description="Sequence of steps to execute")
    description: str = Field(..., description="Brief description of the overall plan")

class CompoundMessageClassifier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    message_type: Literal["simple", "compound"] = Field(
        ...,
        description="Classify if the message is a simple single action or a compound multi-step request"
    ) 