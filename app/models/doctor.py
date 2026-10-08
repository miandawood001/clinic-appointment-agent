from sqlmodel import SQLModel, Field
from typing import Optional


class Doctor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    specialty: str = Field(default="General Dentist")
    fee: int = Field(default=0)
    is_active: bool = Field(default=True)