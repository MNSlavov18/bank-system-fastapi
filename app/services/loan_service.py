from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlite3 import Date
import string

from fastapi import HTTPException, status
from sqlalchemy import DateTime
from sqlalchemy.orm import Session

from app.models.account import BankAccount
from app.models.enums import AccountStatus, LoanStatus
from app.models.loan import Loan, LoanApplication
from app.models.repayment import RepaymentPlan


MONEY = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def _installment_amount(repayment: RepaymentPlan) -> Decimal:
    return _money(repayment.principal_part + repayment.interest_part)


def _loan_to_response(loan: Loan) -> dict:
    application = loan.application
    credit_type = application.credit_type

    mortgage_details = None

    if loan.mortgage_details:
        mortgage_details = {
            "property_address": loan.mortgage_details.property_address,
            "property_value": loan.mortgage_details.property_value,
            "down_payment": loan.mortgage_details.down_payment
        }

    return {
        "loan_id": loan.loan_id,
        "application_id": loan.application_id,
        "client_id": application.client_id,
        "account_id": loan.account_id,
        "credit_type_id": application.credit_type_id,
        "credit_type_name": credit_type.type_name,
        "principal_amount": loan.principal_amount,
        "interest_rate": credit_type.interest_rate,
        "term_months": loan.term_months,
        "start_date": loan.start_date,
        "end_date": loan.end_date,
        "status": loan.status,
        "disbursement_method": loan.disbursement_method,
        "disbursement_account_id": loan.disbursement_account_id,
        "auto_payment_enabled": loan.auto_payment_enabled,
        "payment_account_id": loan.payment_account_id,
        "mortgage_details": mortgage_details
    }


def _repayment_to_response(repayment: RepaymentPlan) -> dict:
    return {
        "installment_id": repayment.installment_id,
        "loan_id": repayment.loan_id,
        "installment_number": repayment.installment_number,
        "due_date": repayment.due_date,
        "installment_amount": _installment_amount(repayment),
        "principal_part": repayment.principal_part,
        "interest_part": repayment.interest_part,
        "remaining_balance": repayment.remaining_balance,
        "is_paid": repayment.is_paid
    }


def get_loan_or_404(loan_id: int, db: Session) -> Loan:
    loan = db.query(Loan).filter(
        Loan.loan_id == loan_id
    ).first()

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found."
        )

    return loan


def get_all_loans(db: Session) -> list[dict]:
    loans = db.query(Loan).order_by(Loan.loan_id.asc()).all()

    return [_loan_to_response(loan) for loan in loans]


def get_loan_by_id(loan_id: int, db: Session) -> dict:
    loan = get_loan_or_404(loan_id, db)

    return _loan_to_response(loan)


def get_loans_by_client(client_id: int, db: Session) -> list[dict]:
    loans = (
        db.query(Loan)
        .join(LoanApplication)
        .filter(LoanApplication.client_id == client_id)
        .order_by(Loan.loan_id.asc())
        .all()
    )

    return [_loan_to_response(loan) for loan in loans]


def get_repayment_plan_by_loan(loan_id: int, db: Session) -> list[dict]:
    get_loan_or_404(loan_id, db)

    repayments = (
        db.query(RepaymentPlan)
        .filter(RepaymentPlan.loan_id == loan_id)
        .order_by(RepaymentPlan.installment_number.asc())
        .all()
    )

    return [_repayment_to_response(repayment) for repayment in repayments]


def get_loan_status(loan_id: int, db: Session) -> dict:
    loan = get_loan_or_404(loan_id, db)

    repayments = (
        db.query(RepaymentPlan)
        .filter(RepaymentPlan.loan_id == loan_id)
        .order_by(RepaymentPlan.installment_number.asc())
        .all()
    )

    paid_repayments = [
        repayment for repayment in repayments
        if repayment.is_paid
    ]

    unpaid_repayments = [
        repayment for repayment in repayments
        if not repayment.is_paid
    ]

    total_paid_amount = sum(
        (_installment_amount(repayment) for repayment in paid_repayments),
        Decimal("0.00")
    )

    remaining_amount = sum(
        (_installment_amount(repayment) for repayment in unpaid_repayments),
        Decimal("0.00")
    )

    next_due_date = None

    if unpaid_repayments:
        next_due_date = unpaid_repayments[0].due_date

    return {
        "loan_id": loan.loan_id,
        "status": loan.status,
        "principal_amount": loan.principal_amount,
        "term_months": loan.term_months,
        "total_installments": len(repayments),
        "paid_installments": len(paid_repayments),
        "unpaid_installments": len(unpaid_repayments),
        "total_paid_amount": _money(total_paid_amount),
        "remaining_amount": _money(remaining_amount),
        "next_due_date": next_due_date
    }


def _get_account_for_installment_payment(loan: Loan) -> BankAccount:
    if loan.auto_payment_enabled and loan.payment_account is not None:
        return loan.payment_account

    return loan.account


def mark_installment_as_paid(
    loan_id: int,
    installment_id: int,
    db: Session
) -> dict:
    loan = get_loan_or_404(loan_id, db)

    if loan.status in [LoanStatus.PAID, LoanStatus.CLOSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installment cannot be paid because the loan is already paid or closed."
        )

    repayment = db.query(RepaymentPlan).filter(
        RepaymentPlan.installment_id == installment_id,
        RepaymentPlan.loan_id == loan_id
    ).first()

    if not repayment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installment not found for this loan."
        )

    if repayment.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installment is already paid."
        )

    account = _get_account_for_installment_payment(loan)

    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installment can be paid only from an active account."
        )

    amount_to_pay = _installment_amount(repayment)

    if account.balance < amount_to_pay:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds in the account to pay this installment."
        )

    account.balance = _money(account.balance - amount_to_pay)
    repayment.is_paid = True

    unpaid_installments_count = db.query(RepaymentPlan).filter(
        RepaymentPlan.loan_id == loan_id,
        RepaymentPlan.is_paid == False,
        RepaymentPlan.installment_id != installment_id
    ).count()

    if unpaid_installments_count == 0:
        loan.status = LoanStatus.PAID

    db.commit()
    db.refresh(repayment)

    return _repayment_to_response(repayment)

def process_due_automatic_payments(loan_id: int, db: Session) -> list[dict]:
    loan = get_loan_or_404(loan_id, db)

    if not loan.auto_payment_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automatic payment is not enabled for this loan."
        )

    if loan.payment_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No payment account is selected for this loan."
        )

    due_installments = (
        db.query(RepaymentPlan)
        .filter(
            RepaymentPlan.loan_id == loan_id,
            RepaymentPlan.is_paid == False,
            RepaymentPlan.due_date <= date.today()
        )
        .order_by(RepaymentPlan.installment_number.asc())
        .all()
    )

    paid_installments = []

    for installment in due_installments:
        amount_to_pay = _installment_amount(installment)

        if loan.payment_account.balance < amount_to_pay:
            break

        loan.payment_account.balance = _money(loan.payment_account.balance - amount_to_pay)
        installment.is_paid = True
        paid_installments.append(installment)

    unpaid_installments_count = db.query(RepaymentPlan).filter(
        RepaymentPlan.loan_id == loan_id,
        RepaymentPlan.is_paid == False
    ).count()

    if unpaid_installments_count == 0 and due_installments:
        loan.status = LoanStatus.PAID

    db.commit()

    return [_repayment_to_response(installment) for installment in paid_installments]

def set_next_unpaid_installment_due_today(
    loan_id: int,
    db: Session
) -> dict:
    loan = get_loan_or_404(loan_id, db)

    if not loan.auto_payment_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automatic payment is not enabled for this loan."
        )

    repayment = (
        db.query(RepaymentPlan)
        .filter(
            RepaymentPlan.loan_id == loan_id,
            RepaymentPlan.is_paid == False
        )
        .order_by(RepaymentPlan.installment_number.asc())
        .first()
    )

    if not repayment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There are no unpaid installments for this loan."
        )

    repayment.due_date = date.today()

    db.commit()
    db.refresh(repayment)

    return _repayment_to_response(repayment)

def process_all_due_automatic_payments(db: Session) -> list[dict]:
    loans = (
        db.query(Loan)
        .filter(
            Loan.auto_payment_enabled == True,
            Loan.payment_account_id.isnot(None),
            Loan.status == LoanStatus.ACTIVE
        )
        .all()
    )

    paid_installments = []

    for loan in loans:
        if loan.payment_account is None:
            continue

        if loan.payment_account.status != AccountStatus.ACTIVE:
            continue

        due_installments = (
            db.query(RepaymentPlan)
            .filter(
                RepaymentPlan.loan_id == loan.loan_id,
                RepaymentPlan.is_paid == False,
                RepaymentPlan.due_date <= date.today()
            )
            .order_by(RepaymentPlan.installment_number.asc())
            .all()
        )

        for installment in due_installments:
            amount_to_pay = _installment_amount(installment)

            if loan.payment_account.balance < amount_to_pay:
                break

            loan.payment_account.balance = _money(
                loan.payment_account.balance - amount_to_pay
            )

            installment.is_paid = True
            paid_installments.append(installment)

        unpaid_installments_count = db.query(RepaymentPlan).filter(
            RepaymentPlan.loan_id == loan.loan_id,
            RepaymentPlan.is_paid == False
        ).count()

        if unpaid_installments_count == 0:
            loan.status = LoanStatus.PAID

    db.commit()

    return [_repayment_to_response(installment) for installment in paid_installments]