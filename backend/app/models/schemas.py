from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InteractionBase(BaseModel):
    hcp_name: str
    interaction_type: str = "Meeting"
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    voice_note_summary: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    hcp_sentiment: str = "Neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    raw_message: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionResponse(InteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    interaction: Optional[InteractionResponse] = None
    extracted_data: Optional[dict] = None

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: dict

class EditInteractionRequest(BaseModel):
    interaction_id: int
    field_name: str
    field_value: str
