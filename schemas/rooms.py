from pydantic import BaseModel, Field
from typing import Optional

class StartCallRequest(BaseModel):
    room_name: Optional[str] = Field(None, description="Unique identifier for the room. If not provided, one will be generated.")
    phone_number: str = Field(..., description="The phone number to dial")
    prompt_content: str = Field(..., description="Content for the agent prompt")
    timeout: int = Field(600, gt=0, description="Time in seconds before empty room closes")
    max_participants: Optional[int] = Field(None, gt=0, le=100, description="Limit max users")