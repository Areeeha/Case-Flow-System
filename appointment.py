from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
import sqlite3
from pathlib import Path

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/template", StaticFiles(directory="template"), name="template")

DB_PATH = 'fyp_database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def insert_appointment(data: dict):
    query = """
        INSERT INTO appointments (
            client_email, client_name, date, time, details, 
            email_subject, email_body, email_for, composed_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (
            data["client_email"], data["client_name"], data["date"], data["time"],
            data.get("details", ""),
            data["email_subject"], data["email_body"],
            data["email_for"], data["composed_by"]
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB insert error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def is_valid_appointment(date: str, time: str) -> bool:
    try:
        appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        return appointment_datetime >= datetime.now()
    except ValueError:
        return False

@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Path("template/appointment.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    else:
        return HTMLResponse(content="<h1>Appointment file not found</h1>", status_code=404)

@app.post("/appointment")
async def schedule_appointment(
    client_email: str = Form(...),
    client_name: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    details: str = Form(""),
    email_subject: str = Form(...),
    email_body: str = Form(...),
    email_for: str = Form(...),
    composed_by: str = Form(...)
):
    if not is_valid_appointment(date, time):
        return JSONResponse(content={"message": "Appointment date/time cannot be in the past."}, status_code=400)

    data = {
        "client_email": client_email,
        "client_name": client_name,
        "date": date,
        "time": time,
        "details": details,
        "email_subject": email_subject,
        "email_body": email_body,
        "email_for": email_for,
        "composed_by": composed_by
    }

    if insert_appointment(data):
        return JSONResponse(content={"message": "Appointment successfully scheduled."}, status_code=200)
    else:
        return JSONResponse(content={"message": "Failed to schedule appointment. Try again later."}, status_code=500)
