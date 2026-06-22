from datetime import date, datetime
from pathlib import Path

from decimal import Decimal
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.account import AccountCreateRequest
from app.schemas.client import ClientUpdateRequest
from app.schemas.loan_application import LoanApplicationCreateRequest
from app.schemas.auth import IndividualRegisterRequest, CorporateRegisterRequest, LoginRequest
from app.services import account_service
from app.services import auth_service
from app.services import credit_type_service
from app.services import client_service
from app.services import loan_application_service
from app.services import loan_service

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_user_friendly_error(error: Exception) -> str:
    if isinstance(error, HTTPException):
        return str(error.detail)

    if isinstance(error, ValidationError):
        first_error = error.errors()[0]
        return str(first_error["msg"]).removeprefix("Value error, ")

    return "Something went wrong. Please check your data and try again."


def get_client_display_name(client_id: int, db: Session) -> str:
    client = client_service.get_client_by_id(client_id, db)

    if client.individual_client:
        return f"{client.individual_client.first_name} {client.individual_client.last_name}"

    if client.corporate_client:
        return f"{client.corporate_client.name} - {client.corporate_client.representative_name}"

    return f"Client {client.client_id}"


def get_logged_in_client_context(client_id: int, user_id: int, db: Session) -> dict:
    return {
        "client_id": client_id,
        "user_id": user_id,
        "client_display_name": get_client_display_name(client_id, db)
    }


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
            context={"error": get_user_friendly_error(e)}
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
            context={"error": get_user_friendly_error(e)}
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
            context={"error": get_user_friendly_error(e)}
        )

@router.get("/dashboard")
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            **get_logged_in_client_context(client_id, user_id, db)
        }
    )


@router.get("/profile")
def profile_page(
    request: Request,
    updated: bool = False,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    client = client_service.get_client_by_id(client_id, db)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            **get_logged_in_client_context(client_id, user_id, db),
            "client": client,
            "updated": updated
        }
    )


@router.post("/profile")
def profile_update_form(
    request: Request,
    email: str = Form(...),
    phone_number: str = Form(...),
    address: str = Form(...),
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    name: str = Form(default=""),
    representative_name: str = Form(default=""),
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        client = client_service.get_client_by_id(client_id, db)

        data = ClientUpdateRequest(
            email=email,
            phone_number=phone_number,
            address=address,
            first_name=first_name or None,
            last_name=last_name or None,
            name=name or None,
            representative_name=representative_name or None
        )

        client_service.update_client(client_id, data, db)

        return RedirectResponse(url="/profile?updated=true", status_code=303)

    except Exception as e:
        client = client_service.get_client_by_id(client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                **get_logged_in_client_context(client_id, user_id, db),
                "client": client,
                "error": get_user_friendly_error(e)
            }
        )


@router.get("/my-accounts")
def my_accounts_page(
    request: Request,
    opened: bool = False,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    accounts = account_service.get_accounts_by_client(client_id, db)

    return templates.TemplateResponse(
        request=request,
        name="my_accounts.html",
        context={
            "accounts": accounts,
            "client_id": client_id,
            "user_id": user_id,
            "client_display_name": get_client_display_name(client_id, db),
            "opened": opened
        }
    )


@router.get("/my-accounts/{account_id}")
def my_account_detail_page(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        account = account_service.get_account_by_id(account_id, client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="account_detail.html",
            context={
                "account": account,
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db)
            }
        )

    except Exception as e:
        accounts = account_service.get_accounts_by_client(client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="my_accounts.html",
            context={
                "accounts": accounts,
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )


@router.get("/my-accounts/{account_id}/add-money")
def add_money_page(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        account = account_service.get_account_by_id(account_id, client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="add_money.html",
            context={
                "account": account,
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db)
            }
        )

    except Exception as e:
        accounts = account_service.get_accounts_by_client(client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="my_accounts.html",
            context={
                "accounts": accounts,
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )


@router.post("/my-accounts/{account_id}/add-money")
def add_money_form(
    request: Request,
    account_id: int,
    amount: Decimal = Form(...),
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        account_service.add_money_to_account(account_id, client_id, Decimal(amount), db)

        return RedirectResponse(url=f"/my-accounts/{account_id}", status_code=303)

    except Exception as e:
        accounts = account_service.get_accounts_by_client(client_id, db)
        return templates.TemplateResponse(
            request=request,
            name="add_money.html",
            context={
                "account": account_service.get_account_by_id(account_id, client_id, db),
                "client_id": client_id,
                "user_id": request.session.get("user_id"),
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )

@router.get("/my-accounts/{account_id}/draw-money")
def draw_money_page(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        account = account_service.get_account_by_id(account_id, client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="draw_money.html",
            context={
                "account": account,
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db)
            }
        )

    except Exception as e:
        accounts = account_service.get_accounts_by_client(client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="my_accounts.html",
            context={
                "accounts": accounts,
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )
@router.post("/my-accounts/{account_id}/draw-money")
def draw_money_form(
    request: Request,
    account_id: int,
    amount: Decimal = Form(...),
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        account_service.draw_money_from_account(account_id, client_id, Decimal(amount), db)

        return RedirectResponse(url=f"/my-accounts/{account_id}", status_code=303)

    except Exception as e:
        accounts = account_service.get_accounts_by_client(client_id, db)
        return templates.TemplateResponse(
            request=request,
            name="draw_money.html",
            context={
                "account": account_service.get_account_by_id(account_id, client_id, db),
                "client_id": client_id,
                "user_id": request.session.get("user_id"),
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )


@router.get("/request-credit")
def request_credit_page(
    request: Request,
    created: bool = False,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="request_credit.html",
        context={
            "accounts": account_service.get_accounts_by_client(client_id, db),
            "credit_types": credit_type_service.get_all_credit_types(db),
            "client_id": client_id,
            "user_id": user_id,
            "client_display_name": get_client_display_name(client_id, db),
            "created": created
        }
    )


@router.post("/request-credit")
def request_credit_form(
    request: Request,
    account_id: int = Form(...),
    credit_type_id: int = Form(...),
    requested_amount: Decimal = Form(...),
    requested_term_months: int = Form(...),
    disbursement_method: str = Form(...),
    disbursement_account_id: str = Form(default=""),
    auto_payment_enabled: bool = Form(False),
    payment_account_id: str = Form(default=""),
    property_address: str = Form(default=""),
    property_value: str = Form(default=""),
    down_payment: str = Form(default=""),
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        if disbursement_method == "CASH":
            disbursement_account_id = ""

        if not auto_payment_enabled:
            payment_account_id = ""

        data = LoanApplicationCreateRequest(
            account_id=account_id,
            credit_type_id=credit_type_id,
            requested_amount=requested_amount,
            requested_term_months=requested_term_months,
            disbursement_method=disbursement_method,
            disbursement_account_id=int(disbursement_account_id) if disbursement_account_id else None,
            auto_payment_enabled=auto_payment_enabled,
            payment_account_id=int(payment_account_id) if payment_account_id else None,
            property_address=property_address,
            property_value=Decimal(property_value) if property_value else None,
            down_payment=Decimal(down_payment) if down_payment else None
        )

        loan_application_service.submit_loan_application(data, client_id, db)

        return RedirectResponse(url="/request-credit?created=true", status_code=303)

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="request_credit.html",
            context={
                "accounts": account_service.get_accounts_by_client(client_id, db),
                "credit_types": credit_type_service.get_all_credit_types(db),
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )


@router.post("/my-accounts/open")
def open_account_form(
    request: Request,
    initial_balance: Decimal = Form(default=Decimal("0.00")),
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        data = AccountCreateRequest(
            client_id=client_id,
            initial_balance=initial_balance
        )
        account_service.open_account(data, db)

        return RedirectResponse(url="/my-accounts?opened=true", status_code=303)

    except Exception as e:
        accounts = account_service.get_accounts_by_client(client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="my_accounts.html",
            context={
                "accounts": accounts,
                "client_id": client_id,
                "user_id": request.session.get("user_id"),
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )

@router.get("/my-loans")
def my_loans_page(
    request: Request,
    paid: bool = False,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    loans = loan_service.get_loans_by_client(client_id, db)

    return templates.TemplateResponse(
        request=request,
        name="my_loans.html",
        context={
            "loans": loans,
            "client_id": client_id,
            "user_id": user_id,
            "client_display_name": get_client_display_name(client_id, db),
            "paid": paid
        }
    )


@router.get("/my-loans/{loan_id}")
def my_loan_detail_page(
    loan_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")
    user_id = request.session.get("user_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    client_id = int(client_id)

    try:
        loan = loan_service.get_loan_by_id(loan_id, db)

        if int(loan["client_id"]) != client_id:
            return RedirectResponse(url="/my-loans", status_code=303)

        repayment_plan = loan_service.get_repayment_plan_by_loan(loan_id, db)
        loan_status = loan_service.get_loan_status(loan_id, db)

        return templates.TemplateResponse(
            request=request,
            name="loan_detail.html",
            context={
                "loan": loan,
                "repayment_plan": repayment_plan,
                "loan_status": loan_status,
                "today": date.today(),
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db)
            }
        )

    except Exception as e:
        print("MY LOAN DETAIL ERROR:", repr(e))

        loans = loan_service.get_loans_by_client(client_id, db)

        return templates.TemplateResponse(
            request=request,
            name="my_loans.html",
            context={
                "loans": loans,
                "client_id": client_id,
                "user_id": user_id,
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )


@router.post("/my-loans/{loan_id}/repayment-plan/{installment_id}/pay")
def pay_installment_form(
    loan_id: int,
    installment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    client_id = request.session.get("client_id")

    if not client_id:
        return RedirectResponse(url="/login", status_code=303)

    try:
        loan = loan_service.get_loan_by_id(loan_id, db)

        if loan["client_id"] != client_id:
            return RedirectResponse(url="/my-loans", status_code=303)

        loan_service.mark_installment_as_paid(loan_id, installment_id, db)

        return RedirectResponse(url=f"/my-loans/{loan_id}?paid=true", status_code=303)

    except Exception as e:
        loan = loan_service.get_loan_by_id(loan_id, db)
        repayment_plan = loan_service.get_repayment_plan_by_loan(loan_id, db)
        loan_status = loan_service.get_loan_status(loan_id, db)

        return templates.TemplateResponse(
            request=request,
            name="loan_detail.html",
            context={
                "loan": loan,
                "repayment_plan": repayment_plan,
                "loan_status": loan_status,
                "today": date.today(),
                "client_id": client_id,
                "user_id": request.session.get("user_id"),
                "client_display_name": get_client_display_name(client_id, db),
                "error": get_user_friendly_error(e)
            }
        )

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
