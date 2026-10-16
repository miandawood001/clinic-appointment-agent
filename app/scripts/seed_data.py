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

    today = datetime.now().replace(minute=0, second=0, microsecond=0)
    schedule = {
        doctor1.id: [10, 11, 15],
        doctor2.id: [14, 16],
    }

    count = 0
    for day in range(1, 8):
        for doctor_id, hours in schedule.items():
            for hour in hours:
                slot_time = (today + timedelta(days=day)).replace(hour=hour)
                session.add(Slot(doctor_id=doctor_id, date=slot_time, is_booked=False))
                count += 1

    session.commit()
    print(f"2 doctors aur {count} slots (agle 7 din) database mein add ho gaye.")