from fastapi import APIRouter, Request, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse
from app.settings import WHATSAPP_VERIFY_TOKEN
from app.agent.conversation import handle_customer_message
from app.agent.whatsapp import send_whatsapp_message

router = APIRouter()


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    return PlainTextResponse(content="Verification failed", status_code=403)


def process_message_background(customer_phone: str, incoming_text: str):
    """Yeh function background mein chalega, Meta ko wait nahi karana padega."""
    reply = handle_customer_message(customer_phone, incoming_text)
    send_result = send_whatsapp_message(customer_phone, reply)
    print("=== WHATSAPP SEND RESULT ===")
    print(send_result)


@router.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            customer_phone = message["from"]
            incoming_text = message["text"]["body"]

            background_tasks.add_task(process_message_background, customer_phone, incoming_text)

    except (KeyError, IndexError):
        pass

    return {"status": "received"}