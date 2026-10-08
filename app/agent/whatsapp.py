import requests
from app.settings import WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID


def send_whatsapp_message(to_number: str, message_text: str):
    """
    Meta WhatsApp API ke through customer ko message bhejta hai.
    """
    url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()