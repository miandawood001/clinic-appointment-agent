from sqlmodel import Session, select
from app.database import engine
from app.models import Message, Appointment, Slot, Doctor

with Session(engine) as session:
    for msg in session.exec(select(Message)).all():
        session.delete(msg)
    for appt in session.exec(select(Appointment)).all():
        session.delete(appt)
    for slot in session.exec(select(Slot)).all():
        session.delete(slot)
    for doc in session.exec(select(Doctor)).all():
        session.delete(doc)
    session.commit()
    print("Sab kuch reset ho gaya: messages, appointments, slots, doctors — sab delete.")