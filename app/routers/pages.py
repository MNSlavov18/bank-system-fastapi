from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.auth import IndividualRegisterRequest, CorporateRegisterRequest, LoginRequest
from app.services import auth_service

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={}
    )


@router.post("/register/individual")
def register_individual_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(...),
    address: str = Form(...),
    egn: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    birth_date: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        data = IndividualRegisterRequest(
            email=email,
            password=password,
            phone_number=phone_number,
            address=address,
            egn=egn,
            first_name=first_name,
            last_name=last_name,
            birth_date=datetime.strptime(birth_date, "%Y-%m-%d").date()
        )

        auth_service.register_individual(data, db)

        return RedirectResponse(url="/login?registered=true", status_code=303)

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": str(e)}
        )


@router.post("/register/corporate")
def register_corporate_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(...),
    address: str = Form(...),
    eik: str = Form(...),
    name: str = Form(...),
    representative_name: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        data = CorporateRegisterRequest(
            email=email,
            password=password,
            phone_number=phone_number,
            address=address,
            eik=eik,
            name=name,
            representative_name=representative_name
        )

        auth_service.register_corporate(data, db)

        return RedirectResponse(url="/login?registered=true", status_code=303)

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": str(e)}
        )


@router.get("/login")
def login_page(request: Request, registered: bool = False):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"registered": registered}
    )


@router.post("/login")
def login_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        data = LoginRequest(email=email, password=password)
        result = auth_service.login(data, db)

        request.session["user_id"] = result["user_id"]
        request.session["client_id"] = result["client_id"]

        return RedirectResponse(url="/dashboard", status_code=303)

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": str(e)}
        )

@router.get("/dashboard")
def dashboard_page(request: Request):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "client_id": client_id,
            "user_id": user_id
        }
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)