from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.loan_application import (
    ClientLoanSummaryResponse,
    LoanApplicationCreateRequest,
    LoanCreatedResponse
)
from app.services import loan_application_service


router = APIRouter(
    prefix="/loan-applications",
    tags=["Loan Applications"]
)


@router.post("", response_model=LoanCreatedResponse)
def submit_loan_application(
    client_id: int,
    data: LoanApplicationCreateRequest,
    db: Session = Depends(get_db)
):
    application, loan, repayments = loan_application_service.submit_loan_application(
        data,
        client_id,
        db
    )

    return LoanCreatedResponse(
        application_id=application.application_id,
        loan_id=loan.loan_id,
        account_id=loan.account_id,
        application_status=application.application_status,
        loan_status=loan.status,
        principal_amount=loan.principal_amount,
        term_months=loan.term_months,
        start_date=loan.start_date,
        end_date=loan.end_date,
        installments_created=len(repayments)
    )


@router.get("/client/{client_id}", response_model=list[ClientLoanSummaryResponse])
def get_client_loans(
    client_id: int,
    db: Session = Depends(get_db)
):
    loans = loan_application_service.get_client_loans(client_id, db)

    return [
        ClientLoanSummaryResponse(
            application_id=loan.application_id,
            loan_id=loan.loan_id,
            account_id=loan.account_id,
            credit_type=loan.application.credit_type.type_name.value,
            principal_amount=loan.principal_amount,
            term_months=loan.term_months,
            loan_status=loan.status,
            start_date=loan.start_date,
            end_date=loan.end_date
        )
        for loan in loans
    ]
