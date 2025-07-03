from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/template", StaticFiles(directory="template"), name="template")

DB_PATH = "D:/university/fyp/fyp_database.db"

@app.on_event("startup")
def ensure_table_exists():
    conn = sqlite3.connect(DB_PATH)
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

@app.get("/", response_class=HTMLResponse)
@app.get("/payment-data", response_class=HTMLResponse)
async def serve_payment_page():
    with open("template/payment_data.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/add-payment", response_class=HTMLResponse)
async def serve_add_payment_form():
    with open("template/add_payment.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/get-payments")
async def get_payments():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT payment_id, case_id, amount, date, status FROM payments")
        rows = cursor.fetchall()
        conn.close()

        payments = [
            {
                "payment_id": row[0],
                "case_id": row[1],
                "amount": row[2],
                "date": row[3],
                "status": row[4],
            }
            for row in rows
        ]
        return {"payments": payments}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete-payment/{payment_id}")
async def delete_payment(payment_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payments WHERE payment_id = ?", (payment_id,))
        conn.commit()
        conn.close()
        return {"message": "Payment deleted successfully."}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

class UpdatePayment(BaseModel):
    case_id: str = Field(..., min_length=1)
    amount: float
    date: str
    status: str

@app.post("/update-payment/{payment_id}")
async def update_payment(payment_id: str, data: UpdatePayment):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM payments WHERE payment_id = ?", (payment_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Payment ID not found.")

        cursor.execute("""
            UPDATE payments
            SET case_id = ?, amount = ?, date = ?, status = ?
            WHERE payment_id = ?
        """, (data.case_id, data.amount, data.date, data.status, payment_id))

        conn.commit()
        conn.close()
        return {"message": "Payment updated successfully."}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
