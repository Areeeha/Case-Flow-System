from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

# Initialize FastAPI app
app = FastAPI()

# Set up template rendering
templates = Jinja2Templates(directory="template")

# Mount static directory for images, CSS, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})
