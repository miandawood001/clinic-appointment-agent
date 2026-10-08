from sqlmodel import Session, select
from app.database import engine
from app.models import Message


def save_message(customer_phone: str, sender: str, text: str, whatsapp_message_id: str = None):
    with Session(engine) as session:
        message = Message(
            customer_phone=customer_phone,
            sender=sender,
            text=text,
            whatsapp_message_id=whatsapp_message_id
        )
        session.add(message)
        session.commit()


def get_conversation_history(customer_phone: str) -> list:
    with Session(engine) as session:
        messages = session.exec(
            select(Message)
            .where(Message.customer_phone == customer_phone)
            .order_by(Message.created_at)
        ).all()

        history = []
        for msg in messages:
            role = "user" if msg.sender == "customer" else "assistant"
            history.append({"role": role, "content": msg.text})
        return history