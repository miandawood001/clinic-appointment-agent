from fastapi import FastAPI
from app.routes.whatsapp import router as whatsapp_router

app = FastAPI(title="Clinic Appointment Agent")

app.include_router(whatsapp_router)

@app.get("/")
def health_check():
    return {"status": "running"}