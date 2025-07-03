from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware  # Add this import
import sqlite3
import shutil
import os

# Initialize FastAPI app
app = FastAPI()

# CORS configuration
origins = [
    "http://127.0.0.1:5500",  # Your frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and template folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/template", StaticFiles(directory="template"), name="template")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="template")

# Serve favicon
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/images/favicon.jpg")

# Redirect root to form
@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/add-employee")

# Ensure image folder exists
UPLOAD_DIR = "static/images/employees"
if not os.path.exists(UPLOAD_DIR):  # Check if the directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)  # Only create if it doesn't exist

# Show form
@app.get("/add-employee", response_class=HTMLResponse)
async def show_add_form(request: Request):
    return templates.TemplateResponse("add_emp.html", {"request": request})

# Handle form POST
@app.post("/add-employee")
async def add_employee(
    request: Request,
    full_name: str = Form(...),
    role: str = Form(...),
    totalCases: int = Form(...),
    casesThisMonth: int = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    practiceAreas: str = Form(...),
    experienceYears: int = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
):
    try:
        # Rename image with employee's name (safe to use as filename)
        image_filename = f"{full_name.replace(' ', '_')}_{image.filename}"
        image_path = f"{UPLOAD_DIR}/{image_filename}"

        # Save the image
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Insert into DB
        conn = sqlite3.connect("fyp_database.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO employees (
                    full_name, role, total_cases, cases_this_month,
                    email, phone, practice_areas, experience_years,
                    description, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                full_name, role, totalCases, casesThisMonth, email, phone,
                practiceAreas, experienceYears, description, image_path
            ))
            conn.commit()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            conn.rollback()  # Rollback in case of an error
        finally:
            conn.close()

        # Return a success response in JSON format
        return JSONResponse(content={"message": "Employee added successfully!"}, status_code=200)
    
    except Exception as e:
        # Log the error
        print(f"Error while adding employee: {str(e)}")
        
        # Return an error response in JSON format
        return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)
    
# Check if email already exists
@app.get("/check-email")
async def check_email(email: str):
    try:
        conn = sqlite3.connect("fyp_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM employees WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()

        return {"exists": bool(result)}
    
    except Exception as e:
        print(f"Error while checking email: {str(e)}")
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
