from typing import Union, List
from pydantic import BaseModel, Field, ConfigDict

class ParameterModification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    parameter: str = Field(..., description="The parameter to modify")
    value: Union[str, float, int, bool] = Field(..., description="The new value for the parameter")

class InputModifier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    modifications: List[ParameterModification] = Field(..., description="List of parameter modifications to apply")

