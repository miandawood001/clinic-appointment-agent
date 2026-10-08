import json
import re
from datetime import datetime
from app.agent.llm_provider import call_llm
from app.agent.tools import (
    TOOLS_SCHEMA,
    check_availability,
    book_appointment,
    get_customer_appointments,
    cancel_appointment,
    reschedule_appointment,
    list_doctors,
)
from app.agent.memory import save_message, get_conversation_history

AVAILABLE_FUNCTIONS = {
    "check_availability": check_availability,
    "book_appointment": book_appointment,
    "get_customer_appointments": get_customer_appointments,
    "cancel_appointment": cancel_appointment,
    "reschedule_appointment": reschedule_appointment,
    "list_doctors": list_doctors,
}

MAX_TOOL_STEPS = 5


def _extract_fake_tool_call(content: str):
    """Kabhi model tool call ko plain text JSON mein likh deta hai — usay pakadte hain."""
    if not content:
        return None
    if not re.search(r'\{.*"name"\s*:\s*"(\w+)".*\}', content, re.DOTALL):
        return None
    try:
        parsed = json.loads(content)
        if "name" in parsed:
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _doctor_mentioned(text: str, doctor_list_text: str) -> bool:
    """Kya customer ne apne message mein kisi doctor ka naam pehle hi likh diya hai?"""
    text = text.lower()
    for line in doctor_list_text.splitlines():
        m = re.search(r"Doctor ID \d+: (.+?) \(", line)
        if not m:
            continue
        tokens = [
            t for t in m.group(1).lower().replace(".", " ").split()
            if t != "dr" and len(t) > 2
        ]
        if any(t in text for t in tokens):
            return True
    return False


def _run_tool(function_name: str, function_args: dict, customer_phone: str) -> str:
    """Tool chalata hai. Phone number hamesha customer ka WhatsApp number use hota hai."""
    if function_name in ("book_appointment", "get_customer_appointments", "cancel_appointment", "reschedule_appointment"):
        function_args["patient_phone"] = customer_phone

    func = AVAILABLE_FUNCTIONS.get(function_name)
    if func is None:
        return f"ERROR: '{function_name}' naam ka koi tool nahi hai."
    try:
        return func(**function_args)
    except TypeError as e:
        return f"ERROR: tool ko sahi arguments nahi mile ({e})."


def handle_customer_message(customer_phone: str, incoming_text: str, wamid: str = None) -> str:
    save_message(customer_phone, "customer", incoming_text, wamid)
    history = get_conversation_history(customer_phone)

    today = datetime.now().strftime("%Y-%m-%d")
    system_message = {
        "role": "system",
        "content": f"""Tum ek hospital ke liye WhatsApp appointment assistant ho. Aaj ki date {today} hai. Customer se friendly Roman Urdu mein baat karo.

RULES
1. Agar customer appointment chahta hai aur usne doctor ka naam nahi bataya, `list_doctors` tool call karo.
2. Doctor ka naam milne ke baad `check_availability` call karo (date YYYY-MM-DD mein, aur us doctor ki doctor_id ke saath).
3. `book_appointment` tabhi call karo jab slot ID aur customer ka naam dono mil chuke hon. Warna pehle poochho.
4. Customer cancel karna chahe to `get_customer_appointments` call karo.
5. Kabhi "confirmed" ya "cancel ho gayi" mat bolo jab tak related tool call na hui ho.
6. Kabhi raw JSON ya code customer ko mat bhejo — sirf seedhe Roman Urdu sentences.
"""
    }

    messages = [system_message] + history
    final_reply = ""
    executed_tools = []
    from_llm = False
    lower_text = incoming_text.lower()

    for _ in range(MAX_TOOL_STEPS):
        response = call_llm(messages, tools=TOOLS_SCHEMA)
        message = response["message"]
        content = message.get("content", "") or ""

        fake_tool_call = None
        if not message.get("tool_calls"):
            fake_tool_call = _extract_fake_tool_call(content)

        # LLM ne tool nahi maanga, seedha jawab diya
        if not (message.get("tool_calls") or fake_tool_call):
            final_reply = content
            from_llm = True
            break

        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            function_name = tool_call["function"]["name"]
            function_args = dict(tool_call["function"]["arguments"])
            assistant_msg = {"role": "assistant", "content": "", "tool_calls": message["tool_calls"]}
        else:
            function_name = fake_tool_call["name"]
            function_args = dict(fake_tool_call.get("parameters", {}))
            assistant_msg = {"role": "assistant", "content": content}

        tool_result = _run_tool(function_name, function_args, customer_phone)
        executed_tools.append(function_name)

        # Jin tools ka jawab code khud bana sakta hai, unke liye LLM par bharosa nahi karte
        direct_reply = None

        if tool_result.startswith("ERROR"):
            pass  # LLM ko dobara try karne ka mauka milega

        elif function_name == "list_doctors":
            if "Doctor ID" not in tool_result:
                direct_reply = tool_result
            elif not _doctor_mentioned(incoming_text, tool_result):
                direct_reply = (
                    f"Yeh hamare available doctors hain:\n\n{tool_result}\n\n"
                    "Kis doctor se appointment lena chahenge?"
                )
            # Agar customer ne doctor ka naam de diya hai to loop aage chalega (availability ke liye)

        elif function_name == "check_availability":
            if "Slot ID" in tool_result:
                direct_reply = (
                    f"Yeh available slots hain:\n\n{tool_result}\n\n"
                    "Konsa slot book karna chahenge? Slot ID aur apna naam bata dein."
                )
            else:
                direct_reply = tool_result

        elif function_name in ("book_appointment", "cancel_appointment", "reschedule_appointment"):
            direct_reply = tool_result

        elif function_name == "get_customer_appointments":
            if tool_result == "NO_APPOINTMENTS":
                direct_reply = "Aapki koi active appointment nahi hai."
            else:
                lines = tool_result.splitlines()
                if "reschedule" in lower_text:
                    direct_reply = (
                        f"Aapki active appointments:\n\n{tool_result}\n\n"
                        "Reschedule ke liye pehle 'cancel kar do' likh dein, phir nayi appointment book kar lete hain."
                    )
                elif "cancel" in lower_text:
                    if len(lines) == 1:
                        appt_id = int(re.search(r"Appointment ID (\d+)", lines[0]).group(1))
                        direct_reply = cancel_appointment(appt_id, customer_phone)
                        executed_tools.append("cancel_appointment")
                    else:
                        direct_reply = (
                            f"Aapki yeh appointments hain:\n\n{tool_result}\n\n"
                            "Konsi cancel karni hai? Appointment ID bata dein."
                        )
                else:
                    direct_reply = f"Aapki active appointments:\n\n{tool_result}"

        if direct_reply is not None:
            final_reply = direct_reply
            break

        messages.append(assistant_msg)
        messages.append({"role": "tool", "content": tool_result})
    else:
        final_reply = "Sorry, is request ko process karne mein masla aa raha hai. Kya aap dobara try kar sakte hain?"

    # Safety net: sirf LLM ke free-text reply ke liye — jhoota "confirmed/cancelled" pakadne ke liye
    if from_llm:
        reply_lower = final_reply.lower()
        claims_booking = any(w in reply_lower for w in ["confirm", "book ho", "booked", "appointment ho gayi"])
        claims_cancel = any(w in reply_lower for w in ["cancel ho", "cancelled", "cancel kar di"])

        if claims_booking and "book_appointment" not in executed_tools and "?" not in final_reply:
            final_reply = "Sorry, abhi appointment book nahi hui. Doctor, slot ID aur apna naam bata dein to main book kar dun."
        elif claims_cancel and "cancel_appointment" not in executed_tools and "?" not in final_reply:
            final_reply = "Sorry, abhi cancel nahi hui. 'Meri appointment cancel kar do' likh kar dobara try karein."

    if not final_reply.strip():
        final_reply = "Sorry, main samajh nahi paya. Kya aap dobara bata sakte hain?"

    save_message(customer_phone, "agent", final_reply)
    return final_reply