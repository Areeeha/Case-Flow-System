from fastapi import FastAPI, UploadFile, File, Response
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import sqlite3
import pytesseract
from PIL import Image
import yake
import re

app = FastAPI()

# Mount static folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/template", StaticFiles(directory="template"), name="template")

DB_PATH = "fyp_database.db"
UPLOAD_FOLDER = "static/uploads/cv_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Utility Functions ---

def get_latest_job():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, description FROM jobs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"title": row[0], "description": row[1]}
    return None

def extract_keywords(text, max_ngram_size=3, num_keywords=15):
    kw_extractor = yake.KeywordExtractor(lan="en", n=max_ngram_size, top=num_keywords)
    keywords = kw_extractor.extract_keywords(text)
    return [kw[0] for kw in keywords]

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path).convert("L")
        image = image.point(lambda x: 0 if x < 140 else 255, '1')  # preprocess
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception:
        return ""

def extract_email(text):
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    return match.group() if match else "Email not found"

# --- API Routes ---

@app.get("/latest-job")
async def latest_job():
    job = get_latest_job()
    if job:
        return job
    return JSONResponse(status_code=404, content={"message": "No job postings found."})

@app.post("/upload-cv")
async def upload_cv(cv_image: UploadFile = File(...)):
    allowed_ext = {".jpg", ".jpeg", ".png"}
    filename = cv_image.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_ext:
        return JSONResponse(status_code=400, content={"error": "Invalid file type. Only JPG, JPEG, PNG allowed."})

    save_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(cv_image.file, buffer)
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Failed to save CV file."})

    job = get_latest_job()
    if not job:
        return JSONResponse(status_code=404, content={"error": "No job posting found in the database."})

    job_keywords = extract_keywords(job["description"])
    cv_text = extract_text_from_image(save_path)
    cv_keywords = extract_keywords(cv_text)
    email = extract_email(cv_text)

    # Match
    job_kw_set = set(k.lower() for k in job_keywords)
    cv_kw_set = set(k.lower() for k in cv_keywords)
    matched_keywords = job_kw_set & cv_kw_set

    threshold = 5
    is_shortlisted = len(matched_keywords) >= threshold
    score = len(matched_keywords) / max(len(job_kw_set), 1)

    return {
        "filename": filename,
        "email": email,
        "common_keywords": sorted(matched_keywords),
        "score": round(score, 2),
        "shortlisted": is_shortlisted,
        "job_keywords": job_keywords,
        "cv_keywords": cv_keywords
    }

@app.get("/upload_cv", response_class=HTMLResponse)
async def upload_cv_page():
    with open("template/upload_cv.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/")
async def root():
    return RedirectResponse(url="/upload_cv")

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)
