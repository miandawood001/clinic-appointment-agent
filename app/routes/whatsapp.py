from fastapi import APIRouter, Request, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select
from app.settings import WHATSAPP_VERIFY_TOKEN
from app.agent.conversation import handle_customer_message
from app.agent.whatsapp import send_whatsapp_message
from app.database import engine
from app.models import Message
import traceback

router = APIRouter()


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """Meta yahan se webhook URL verify karta hai."""
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    return PlainTextResponse(content="Verification failed", status_code=403)


def process_message_background(customer_phone: str, incoming_text: str, wamid: str):
    """Background mein agent chalata hai, taake Meta ko turant 200 mil jaye."""
    try:
        reply = handle_customer_message(customer_phone, incoming_text, wamid)
    except Exception:
        traceback.print_exc()
        reply = "Sorry, abhi system mein masla hai. Thodi der baad dobara try karein."

    send_result = send_whatsapp_message(customer_phone, reply)
    print("=== WHATSAPP SEND RESULT ===")
    print(send_result)


@router.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" in value:
            message = value["messages"][0]
            customer_phone = message["from"]
            incoming_text = message["text"]["body"]
            wamid = message["id"]

            # Duplicate check: yeh message pehle process ho chuka hai?
            with Session(engine) as session:
                existing = session.exec(
                    select(Message).where(Message.whatsapp_message_id == wamid)
                ).first()
                if existing:
                    print(f"Duplicate message ignore kiya: {wamid}")
                    return {"status": "duplicate ignored"}

            background_tasks.add_task(
                process_message_background, customer_phone, incoming_text, wamid
            )

    except (KeyError, IndexError):
        pass

    return {"status": "received"}