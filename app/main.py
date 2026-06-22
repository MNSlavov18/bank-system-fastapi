from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.services.scheduler_service import start_scheduler, stop_scheduler

from app.database.database import SessionLocal
from app.routers import auth, pages, accounts, clients, credit_types, loan_applications, loans
from app.services.credit_type_service import seed_credit_types

app = FastAPI(
    title="Bank System API",
    description="Web-based banking system for managing clients, accounts and loans.",
    version="1.0.0"
)

app.add_middleware(
    SessionMiddleware,
    secret_key="bank-system-secret-key"
)

app.include_router(auth.router)
app.include_router(pages.router)    
app.include_router(accounts.router)
app.include_router(clients.router)
app.include_router(credit_types.router)
app.include_router(loan_applications.router)
app.include_router(loans.router)



app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def seed_fixed_credit_types():
    db = SessionLocal()

    try:
        seed_credit_types(db)
    finally:
        db.close()


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={}
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()
