from pydantic import BaseModel, Field
from enum import Enum 
from typing import List, Optional

class StateType(str, Enum):
    LOCATION= "location"
    CONDITION= "condition"
    CIRCUMSTANCE= "circumstance"
    ACTION= "action"
    #EMOTION= "emotion"

    @property
    def edge_label(self) -> str:
        mapping = {
            StateType.LOCATION: "AT_LOCATION",
            StateType.ACTION: "DO_ACTION",
            StateType.CONDITION: "HAS_CONDITION",
            StateType.CIRCUMSTANCE: "IS_SAFE",
            #StateType.EMOTION: "HAS_EMOTION",
        }
        return mapping[self]    

class StateNode(BaseModel):
    name: str 
    type: StateType
    description: Optional[str] = None

class TransitionEdge(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    condition_ref: str
    probability: Optional[float] = 1.0

class GameSchema(BaseModel):
    states: List[StateNode]
    transition: List[TransitionEdge]
    model_config = {"populate_by_name": True}