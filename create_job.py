from fastapi import FastAPI, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import sqlite3

app = FastAPI()

# Mount static folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/template", StaticFiles(directory="template"), name="template")

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)  # No Content

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("template/create_job.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

DB_PATH = "fyp_database.db"

def get_db():
    # Fix: Allow connection usage across threads
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                keywords TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

init_db()

@app.post("/create-job")
async def create_job(
    title: str = Form(...),
    description: str = Form(...),
    keywords: str = Form(default=""),
    conn: sqlite3.Connection = Depends(get_db)
):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (title, description, keywords) VALUES (?, ?, ?)",
            (title, description, keywords)
        )
        conn.commit()
        return JSONResponse({"message": "Job posted successfully!"})
    except Exception as e:
        print("Database insert error:", e)
        return JSONResponse({"message": "Error posting job. Please try again."}, status_code=500)

@app.get("/latest-job")
async def latest_job(conn: sqlite3.Connection = Depends(get_db)):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, description, keywords FROM jobs ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            job = {
                "title": row[0],
                "description": row[1],
                "keywords": row[2]
            }
            return JSONResponse(job)
        else:
            return JSONResponse({"message": "No job postings found."}, status_code=404)
    except Exception as e:
        print("DB fetch error:", e)
        return JSONResponse({"message": "Failed to fetch latest job."}, status_code=500)
