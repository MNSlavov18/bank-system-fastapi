from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import auth, pages

app = FastAPI(
    title="Bank System API",
    description="Web-based banking system for managing clients, accounts and loans.",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(pages.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def home():
    return {"message": "Bank System API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}