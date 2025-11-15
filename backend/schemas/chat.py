"""Chat schemas."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message schema."""
    message_id: str
    session_id: str
    user_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    tokens_used: Optional[int] = None


class ChatRequest(BaseModel):
    """Request schema for chat message."""
    prompt: str
    session_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ChatResponse(BaseModel):
    """Response schema for chat message."""
    message_id: str
    session_id: str
    response: str
    tokens_used: int
    cached: bool = False
    timestamp: datetime


class ChatHistory(BaseModel):
    """Chat history schema."""
    session_id: str
    user_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
