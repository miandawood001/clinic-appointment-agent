from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slot_id: int = Field(foreign_key="slot.id")
    patient_name: str
    patient_phone: str
    status: str = Field(default="confirmed")   # confirmed / cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)