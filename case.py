from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/css/images/favicon.jpg")


@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/create-case")

@app.get("/create-case", response_class=HTMLResponse)
async def show_case_form(request: Request):
    return templates.TemplateResponse("Case.html", {"request": request})

@app.get("/get-associates/{case_type}")
async def get_associates(case_type: str):
    conn = sqlite3.connect("fyp_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM employees WHERE role = ?", (case_type,))
    rows = cursor.fetchall()
    conn.close()
    associates = [{"name": row[0]} for row in rows]
    return {"associates": associates}

@app.get("/next-case-id")
async def get_next_case_id():
    conn = sqlite3.connect("fyp_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(caseId) FROM cases")
    result = cursor.fetchone()
    conn.close()
    next_id = (result[0] + 1) if result[0] else 101
    return {"caseId": next_id}

@app.post("/submit-case")
async def submit_case(
    caseId: int = Form(...),
    caseTitle: str = Form(...),
    description: str = Form(...),
    caseType: str = Form(...),
    priority: str = Form(...),
    startDate: str = Form(...),
    dueDate: str = Form(...),
    associate: str = Form(...),
    notes: str = Form(None)
):
    try:
        conn = sqlite3.connect("fyp_database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO cases (
                caseId, caseTitle, description, caseType, priority,
                startDate, dueDate, associate, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            caseId, caseTitle, description, caseType, priority,
            startDate, dueDate, associate, notes
        ))

        conn.commit()
        conn.close()
        return JSONResponse(content={"message": f"Case #{caseId} created successfully!"})

    except Exception as e:
        return JSONResponse(content={"message": f"Failed to create case: {e}"}, status_code=500)
