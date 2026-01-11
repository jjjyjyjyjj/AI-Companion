from pydantic import BaseModel
from uuid import UUID

class StartSessionRequest(BaseModel):
    session_topic: str

class SessionAttentionSummaryRequest(BaseModel):
    session_id: UUID
    seconds_focused: int      
    seconds_distracted: int   
    avg_attention: float
    # samples_count: int
