from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import sqlite3
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and template folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/template", StaticFiles(directory="template"), name="template")

# Serve favicon safely
@app.get("/favicon.ico")
async def favicon():
    favicon_path = "static/images/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        raise HTTPException(status_code=404, detail="Favicon not found.")

# Root route now serves Contact Us page directly
@app.get("/", response_class=HTMLResponse)
async def root():
    contact_html_path = "template/contact.html"
    if os.path.exists(contact_html_path):
        return FileResponse(contact_html_path, media_type="text/html")
    else:
        return HTMLResponse("<h2>Contact page not found.</h2>", status_code=404)

# Contact page route (optional; you can still access /contact explicitly)
@app.get("/contact", response_class=HTMLResponse)
async def get_contact_page():
    contact_html_path = "template/contact.html"
    if os.path.exists(contact_html_path):
        return FileResponse(contact_html_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Contact page not found.")

# SQLite DB connection utility
def get_db_connection():
    try:
        conn = sqlite3.connect("fyp_database.db")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# Pydantic model for contact form
class ContactForm(BaseModel):
    full_name: str
    email: EmailStr
    message: str

# Contact form submission endpoint
@app.post("/contact")
async def contact(form_data: ContactForm):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            INSERT INTO contacts (full_name, email, message)
            VALUES (?, ?, ?)
        ''', (form_data.full_name, form_data.email, form_data.message))

        conn.commit()
        return {"message": "Your message has been received!"}

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()
