from datetime import datetime
from sqlmodel import Session, select
from app.database import engine
from app.models import Slot, Doctor, Appointment


def check_availability(date: str, doctor_id: int) -> str:
    """
    Diye gaye doctor ke, diye gaye date pe available (free) slots dhundta hai.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return "Date format sahi nahi hai. Please YYYY-MM-DD format mein do."

    with Session(engine) as session:
        slots = session.exec(
            select(Slot).where(Slot.is_booked == False, Slot.doctor_id == doctor_id)
        ).all()

        matching_slots = [s for s in slots if s.date.date() == target_date]

        if not matching_slots:
            return f"{date} ko is doctor ke paas koi slot available nahi hai."

        result = []
        for slot in matching_slots:
            result.append(f"Slot ID {slot.id}: {slot.date.strftime('%I:%M %p')}")
        return "\n".join(result)


def book_appointment(slot_id: int, patient_name: str, patient_phone: str) -> str:
    """
    Diye gaye slot ko book karta hai aur doctor/date/time ke saath confirmation deta hai.
    """
    with Session(engine) as session:
        slot = session.get(Slot, slot_id)

        if not slot:
            return "Yeh slot exist nahi karta."
        if slot.is_booked:
            return "Yeh slot already booked hai."

        doctor = session.get(Doctor, slot.doctor_id)
        doctor_name = doctor.name if doctor else "doctor"
        fee_text = f" Fee: Rs. {doctor.fee}." if doctor else ""
        date_text = slot.date.strftime("%Y-%m-%d")
        time_text = slot.date.strftime("%I:%M %p")

        slot.is_booked = True
        session.add(slot)

        appointment = Appointment(
            slot_id=slot_id,
            patient_name=patient_name,
            patient_phone=patient_phone
        )
        session.add(appointment)
        session.commit()

        return (
            f"Appointment confirm ho gayi hai! {patient_name} ki appointment "
            f"{doctor_name} ke saath {date_text} ko {time_text} par book hui hai.{fee_text}"
        )
        


def get_customer_appointments(patient_phone: str) -> str:
    """
    Diye gaye phone number ki saari active (confirmed) appointments dhundta hai.
    """
    with Session(engine) as session:
        appointments = session.exec(
            select(Appointment).where(
                Appointment.patient_phone == patient_phone,
                Appointment.status == "confirmed"
            )
        ).all()

        if not appointments:
            return "NO_APPOINTMENTS"

        result = []
        for appt in appointments:
            slot = session.get(Slot, appt.slot_id)
            if slot:
                result.append(f"Appointment ID {appt.id}: {slot.date.strftime('%Y-%m-%d %I:%M %p')}")
        return "\n".join(result)


def cancel_appointment(appointment_id: int, patient_phone: str) -> str:
    """
    Diye gaye Appointment ID ki booking cancel karta hai — sirf tab jab
    yeh appointment isi patient_phone ki ho.
    """
    with Session(engine) as session:
        appointment = session.get(Appointment, appointment_id)

        if not appointment:
            return "Yeh appointment exist nahi karti."
        if appointment.patient_phone != patient_phone:
            return "Yeh appointment aapke number se linked nahi hai."
        if appointment.status == "cancelled":
            return "Yeh appointment pehle hi cancel ho chuki hai."

        appointment.status = "cancelled"
        session.add(appointment)

        slot = session.get(Slot, appointment.slot_id)
        if slot:
            slot.is_booked = False
            session.add(slot)

        session.commit()
        return f"Appointment ID {appointment_id} successfully cancel ho gayi hai."



def list_doctors() -> str:
    """
    Saare active doctors ki list deta hai, naam, specialty aur fee ke saath.
    """
    with Session(engine) as session:
        doctors = session.exec(
            select(Doctor).where(Doctor.is_active == True)
        ).all()

        if not doctors:
            return "Filhal koi doctor available nahi hai."

        result = []
        for doc in doctors:
            result.append(f"Doctor ID {doc.id}: {doc.name} ({doc.specialty}) - Fee: Rs. {doc.fee}")
        return "\n".join(result)

def reschedule_appointment(appointment_id: int, new_slot_id: int, patient_phone: str) -> str:
    """
    Purani appointment cancel karke naya slot ek hi transaction mein book karta hai.
    Agar naya slot available na ho, purani appointment waisi hi rehti hai (safe rollback).
    """
    with Session(engine) as session:
        old_appointment = session.get(Appointment, appointment_id)

        if not old_appointment:
            return "Yeh purani appointment exist nahi karti."
        if old_appointment.patient_phone != patient_phone:
            return "Yeh appointment aapke number se linked nahi hai."
        if old_appointment.status == "cancelled":
            return "Yeh appointment pehle hi cancel ho chuki hai."

        new_slot = session.get(Slot, new_slot_id)
        if not new_slot:
            return "Naya slot exist nahi karta — purani appointment waisi hi hai."
        if new_slot.is_booked:
            return "Yeh naya slot already booked hai — purani appointment waisi hi hai, koi aur slot chunein."

        old_slot = session.get(Slot, old_appointment.slot_id)
        if old_slot:
            old_slot.is_booked = False
            session.add(old_slot)

        old_appointment.status = "cancelled"
        session.add(old_appointment)

        new_slot.is_booked = True
        session.add(new_slot)

        new_appointment = Appointment(
            slot_id=new_slot_id,
            patient_name=old_appointment.patient_name,
            patient_phone=patient_phone
        )
        session.add(new_appointment)
        session.commit()

        doctor = session.get(Doctor, new_slot.doctor_id)
        doctor_name = doctor.name if doctor else "doctor"
        date_text = new_slot.date.strftime("%Y-%m-%d")
        time_text = new_slot.date.strftime("%I:%M %p")

        return (
            f"Reschedule ho gaya! {old_appointment.patient_name} ki appointment ab "
            f"{doctor_name} ke saath {date_text} ko {time_text} par hai."
        )

# Yeh schema Ollama ko batata hai konse tools available hain
TOOLS_SCHEMA = [
        {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Kisi specific doctor ke, kisi date pe available appointment slots check karta hai",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date jismein slots check karne hain, e.g. '2026-08-28'"},
                    "doctor_id": {"type": "integer", "description": "Jis doctor ke slots check karne hain uski ID"}
                },
                "required": ["date", "doctor_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Ek specific slot ko book karta hai patient ke naam par",
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id": {"type": "integer", "description": "Jo slot book karna hai uski ID"},
                    "patient_name": {"type": "string", "description": "Patient ka naam"},
                    "patient_phone": {"type": "string", "description": "Patient ka phone number"}
                },
                "required": ["slot_id", "patient_name", "patient_phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_appointments",
            "description": "Diye gaye phone number ke liye saari active appointments ko retrieve karta hai",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_phone": {"type": "string", "description": "Patient ka phone number"}
                },
                "required": ["patient_phone"]
            }
        }
    },
        {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Diye gaye Appointment ID ki booking cancel karta hai aur slot ko free kar deta hai",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Jo appointment cancel karni hai uski ID"},
                    "patient_phone": {"type": "string", "description": "Patient ka phone number (automatically fill hota hai)"}
                },
                "required": ["appointment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_doctors",
            "description": "Saare active doctors ki list deta hai, naam, specialty aur fee ke saath",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Purani appointment cancel karke naya slot ek saath book karta hai",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Purani appointment ki ID"},
                    "new_slot_id": {"type": "integer", "description": "Naya slot jo book karna hai"},
                    "patient_phone": {"type": "string", "description": "Patient ka phone number (automatically fill hota hai)"}
                },
                "required": ["appointment_id", "new_slot_id"]
            }
        }
    }

]