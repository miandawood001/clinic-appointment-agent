from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_phone: str
    sender: str
    text: str
    whatsapp_message_id: Optional[str] = Field(default=None, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)