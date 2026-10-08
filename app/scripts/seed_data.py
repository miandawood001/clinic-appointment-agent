from sqlmodel import Session
from datetime import datetime, timedelta
from app.database import engine
from app.models import Doctor, Slot

with Session(engine) as session:
    doctor1 = Doctor(name="Dr. Ahmed", specialty="Dentist", fee=1500)
    doctor2 = Doctor(name="Dr. Sara", specialty="Skin Specialist", fee=2000)
    session.add(doctor1)
    session.add(doctor2)
    session.commit()
    session.refresh(doctor1)
    session.refresh(doctor2)

    tomorrow = datetime.now() + timedelta(days=1)

    slots_data = [
        (doctor1.id, tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)),
        (doctor1.id, tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)),
        (doctor2.id, tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)),
        (doctor2.id, tomorrow.replace(hour=16, minute=0, second=0, microsecond=0)),
    ]

    for doctor_id, slot_time in slots_data:
        slot = Slot(doctor_id=doctor_id, date=slot_time, is_booked=False)
        session.add(slot)

    session.commit()
    print(f"2 doctors aur {len(slots_data)} slots database mein add ho gaye.")