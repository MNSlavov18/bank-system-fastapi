from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.loan import (
    LoanResponse,
    LoanStatusResponse,
    RepaymentInstallmentResponse
)
from app.services import loan_service


router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)


@router.get("", response_model=list[LoanResponse])
def get_all_loans(db: Session = Depends(get_db)):
    return loan_service.get_all_loans(db)


@router.get("/client/{client_id}", response_model=list[LoanResponse])
def get_loans_by_client(
    client_id: int,
    db: Session = Depends(get_db)
):
    return loan_service.get_loans_by_client(client_id, db)


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan_by_id(
    loan_id: int,
    db: Session = Depends(get_db)
):
    return loan_service.get_loan_by_id(loan_id, db)


@router.get("/{loan_id}/status", response_model=LoanStatusResponse)
def get_loan_status(
    loan_id: int,
    db: Session = Depends(get_db)
):
    return loan_service.get_loan_status(loan_id, db)


@router.get("/{loan_id}/repayment-plan", response_model=list[RepaymentInstallmentResponse])
def get_repayment_plan_by_loan(
    loan_id: int,
    db: Session = Depends(get_db)
):
    return loan_service.get_repayment_plan_by_loan(loan_id, db)


@router.patch(
    "/{loan_id}/repayment-plan/{installment_id}/pay",
    response_model=RepaymentInstallmentResponse
)
def mark_installment_as_paid(
    loan_id: int,
    installment_id: int,
    db: Session = Depends(get_db)
):
    return loan_service.mark_installment_as_paid(loan_id, installment_id, db)