from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender (user, assistant)")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="The message from the user")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="Previous chat history")
    ra: str = Field(default="01493115", description="Student ID (RA)")
    coligada: int = Field(default=1, description="Coligada ID")
    habilitacao: int = Field(default=18486, description="Habilitacao ID")
    is_initial_greeting: bool = Field(default=False, description="True if this is the first proactive greeting")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="The response from the agent")
    internal_discussion: List[Dict[str, Any]] = Field(default_factory=list, description="Internal agent communication history")
