from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Slot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctor.id")
    date: datetime
    is_booked: bool = Field(default=False)