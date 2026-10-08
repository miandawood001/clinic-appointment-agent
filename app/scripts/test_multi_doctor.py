from sqlmodel import Session, select
from app.database import engine
from app.models import Doctor, Slot
from app.agent.conversation import handle_customer_message

customer_phone = "03005556666"

with Session(engine) as session:
    sara = session.exec(select(Doctor).where(Doctor.name == "Dr. Sara")).first()
    slot = session.exec(
        select(Slot).where(Slot.doctor_id == sara.id, Slot.is_booked == False)
    ).first()
    slot_id = slot.id

steps = [
    "Assalam o Alaikum, mujhe appointment chahiye",
    "Dr. Sara se milna hai, kal ke slots dikhao",
    f"Slot ID {slot_id} book kar do, mera naam Ayesha hai",
    "Meri appointment cancel kar do",
]

for i, text in enumerate(steps, start=1):
    print(f"=== Message {i}: {text} ===")
    print(f"Agent: {handle_customer_message(customer_phone, text)}\n")