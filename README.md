# Clinic Appointment Booking Agent

AI-powered WhatsApp assistant that lets patients book, view, and cancel appointments with a hospital's doctors — entirely through natural conversation, no app or website needed.

## What it does

A patient messages the clinic's WhatsApp number. The AI agent:
- Lists available doctors with their specialty and consultation fee
- Shows a doctor's open appointment slots for a given date
- Books an appointment once the patient confirms a slot and shares their name
- Looks up and cancels a patient's existing appointment on request

All of this happens in plain conversational language (Roman Urdu/English) — the agent understands intent, calls the right backend function, and replies naturally.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL + SQLModel + Alembic migrations
- **AI Agent:** Local LLM (Ollama / Llama 3.1 8B) with function/tool calling
- **Messaging:** Meta WhatsApp Business Cloud API
- **Infrastructure:** Docker (PostgreSQL container)

## Architecture
Patient's WhatsApp
│
▼
Meta WhatsApp Cloud API
│
▼
FastAPI Webhook (app/routes/whatsapp.py)
│
▼
Agent Core (app/agent/conversation.py)
│ │
▼ ▼
LLM Tool-Calling PostgreSQL Database
(check availability, book, cancel, list doctors)

### Key design decisions

- **Tool-calling with safety nets:** The LLM decides *which* action to take, but critical replies (booking confirmations, cancellations, doctor lists) are generated directly from database results — not from the LLM's own text — to prevent it from claiming an action succeeded when it didn't.
- **Duplicate-message protection:** WhatsApp retries webhook deliveries if a response is slow. Every inbound message is tagged with its WhatsApp message ID and de-duplicated before processing.
- **Background processing:** Incoming messages are acknowledged to WhatsApp immediately and processed asynchronously, so slow LLM responses never cause Meta to resend the same message.
- **Phone-verified actions:** A patient can only cancel their own appointment — the backend checks the requester's phone number against the appointment record before allowing changes.

## Project Structure
app/
├── agent/ # LLM logic, tool definitions, conversation flow, WhatsApp sender
├── models/ # Database tables (Doctor, Slot, Appointment, Message)
├── routes/ # FastAPI webhook endpoint
├── scripts/ # Database seeding and reset utilities
├── database.py # DB connection
├── main.py # FastAPI app entry point
└── settings.py # Environment variable loading

alembic/ # Database migrations
docker-compose.yml # PostgreSQL container config

## Setup

### Prerequisites
- Python 3.11+
- Docker Desktop
- [Ollama](https://ollama.com) with a model pulled (e.g. `ollama pull llama3.1:8b`)
- A Meta Developer account with WhatsApp Business API access

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd clinic-appointment-agent

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy the environment template and fill in your own values
cp .env.example .env
```

### Database setup

```bash
# Start PostgreSQL
docker compose up -d

# Run migrations
alembic upgrade head

# Seed sample doctors and slots
python -m app.scripts.seed_data
```

### Run the server

```bash
uvicorn app.main:app --reload
```

Expose it publicly (for WhatsApp webhooks) using a tool like [ngrok](https://ngrok.com), then configure the callback URL in your Meta Developer dashboard.

## Development Utilities

- `python -m app.scripts.seed_data` — adds sample doctors and appointment slots
- `python -m app.scripts.full_reset` — wipes all messages, appointments, slots, and doctors (development only — do not run against real data)
- `python -m app.scripts.test_multi_doctor` — runs a scripted end-to-end conversation test without needing WhatsApp

## Status

Core booking flow (list doctors → check availability → book → cancel) is stable and tested end-to-end. Reschedule-in-one-message and production deployment are planned next steps.

## Author

Built by Dawood as a portfolio project exploring agentic AI, tool-calling LLMs, and real-world WhatsApp Business API integration.