from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and template folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/template", StaticFiles(directory="template"), name="template")

# Path to your database
DB_PATH = "D:/university/fyp/fyp_database.db"

# ✅ Create payments table if it doesn't exist
def ensure_payments_table():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    ensure_payments_table()

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    with open("template/add_payment.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/add-payment", response_class=HTMLResponse)
async def serve_add_payment_form():
    html_path = os.path.join("template", "add_payment.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
from pydantic import BaseModel

class Payment(BaseModel):
    payment_id: str
    case_id: str
    amount: float
    date: str
    status: str

@app.post("/add-payment")
async def add_payment(payment: Payment):  # ✅ use your model here
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM payments WHERE payment_id = ?", (payment.payment_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Payment ID already exists.")

        cursor.execute("""
            INSERT INTO payments (payment_id, case_id, amount, date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (payment.payment_id, payment.case_id, payment.amount, payment.date, payment.status))

        conn.commit()
        conn.close()
        return {"message": "Payment added successfully."}

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/payment-data", response_class=HTMLResponse)
async def serve_payment_data_page():
    html_path = os.path.join("template", "payment_data.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
