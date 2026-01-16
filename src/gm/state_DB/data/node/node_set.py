
# [Node] RDB - 정적 정보 (Pydantic Model)
class StateNode(BaseModel):
    id: str  
    name: str
    type: str  
    description: List[str]  