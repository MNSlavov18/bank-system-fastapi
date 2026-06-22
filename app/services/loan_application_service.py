import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.account import BankAccount
from app.models.failedCredit import FailedCredit
from app.models.enums import AccountStatus, CreditTypeName, LoanApplicationStatus, LoanStatus
from app.models.loan import Loan, LoanApplication
from app.models.mortgage import MortgageDetails
from app.models.repayment import RepaymentPlan
from app.schemas.loan_application import LoanApplicationCreateRequest
from app.services import account_service, credit_type_service
from app.models.credit import CreditType


MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])

    return date(year, month, day)


def _validate_active_account(account: BankAccount) -> None:
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credit can be requested only for an active account."
        )


def _validate_credit_limits(
    data: LoanApplicationCreateRequest,
    credit_type: CreditType
) -> None:
    if data.requested_amount > credit_type.max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested amount is higher than the maximum amount for this credit type."
        )

    if data.requested_term_months > credit_type.max_term_months:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested term is longer than the maximum term for this credit type."
        )


def _validate_consumer_credit(
    data: LoanApplicationCreateRequest,
    account: BankAccount,
    db: Session
) -> None:
    minimum_balance = _money(data.requested_amount * Decimal("0.10"))

    if account.balance < minimum_balance:
        failed_credit = FailedCredit(
            type_name=CreditTypeName.CONSUMER,
            requested_amount=data.requested_amount,
            requested_term_months=data.requested_term_months,
            failure_reason="Account balance must cover at least 10% of the requested credit amount.",
            failed_at=date.today(),
            account_id=account.account_id,
            client_id=account.client_id
        )
        db.add(failed_credit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account balance must cover at least 10% of the requested credit amount."
        )


def _validate_mortgage_credit(
    data: LoanApplicationCreateRequest,
    account: BankAccount
) -> None:
    if not data.property_address or data.property_value is None or data.down_payment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mortgage requests require property address, property value, and down payment."
        )

    if data.down_payment > account.balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account balance is not enough for the mortgage down payment."
        )

    if data.requested_amount > data.property_value - data.down_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested mortgage amount cannot be higher than property value minus down payment."
        )


def _create_repayment_plan(
    loan: Loan,
    annual_interest_rate: Decimal,
    db: Session
) -> list[RepaymentPlan]:
    monthly_interest_rate = annual_interest_rate / Decimal("100") / Decimal("12")
    remaining_balance = loan.principal_amount
    repayments = []

    if monthly_interest_rate == 0:
        monthly_payment = _money(loan.principal_amount / Decimal(loan.term_months))
    else:
        rate_factor = (Decimal("1") + monthly_interest_rate) ** loan.term_months
        monthly_payment = _money(
            loan.principal_amount
            * monthly_interest_rate
            * rate_factor
            / (rate_factor - Decimal("1"))
        )

    for installment_number in range(1, loan.term_months + 1):
        interest_part = _money(remaining_balance * monthly_interest_rate)

        if installment_number == loan.term_months:
            current_principal = _money(remaining_balance)
        else:
            current_principal = _money(monthly_payment - interest_part)

        remaining_balance = _money(remaining_balance - current_principal)

        repayment = RepaymentPlan(
            installment_number=installment_number,
            due_date=_add_months(loan.start_date, installment_number),
            principal_part=current_principal,
            interest_part=interest_part,
            remaining_balance=remaining_balance,
            is_paid=False,
            loan_id=loan.loan_id
        )

        db.add(repayment)
        repayments.append(repayment)

    return repayments


def submit_loan_application(
    data: LoanApplicationCreateRequest,
    client_id: int,
    db: Session
) -> tuple[LoanApplication, Loan, list[RepaymentPlan]]:
    account = account_service.get_account_by_id(data.account_id, client_id, db)
    credit_type = credit_type_service.get_credit_type_by_id(data.credit_type_id, db)

    _validate_active_account(account)
    _validate_credit_limits(data, credit_type)

    if credit_type.type_name == CreditTypeName.MORTGAGE:
        _validate_mortgage_credit(data, account)
    else:
        _validate_consumer_credit(data, account, db)

    try:
        application = LoanApplication(
            requested_amount=data.requested_amount,
            requested_term_months=data.requested_term_months,
            application_status=LoanApplicationStatus.APPROVED,
            client_id=client_id,
            credit_type_id=credit_type.credit_type_id
        )

        db.add(application)
        db.flush()

        start_date = date.today()
        loan = Loan(
            principal_amount=data.requested_amount,
            term_months=data.requested_term_months,
            start_date=start_date,
            end_date=_add_months(start_date, data.requested_term_months),
            status=LoanStatus.ACTIVE,
            application_id=application.application_id,
            account_id=account.account_id
        )

        db.add(loan)
        db.flush()

        if credit_type.type_name == CreditTypeName.MORTGAGE:
            account.balance = _money(account.balance - data.down_payment)
            db.add(MortgageDetails(
                loan_id=loan.loan_id,
                property_address=data.property_address,
                property_value=data.property_value,
                down_payment=data.down_payment
            ))

        repayments = _create_repayment_plan(loan, credit_type.interest_rate, db)

        db.commit()
        db.refresh(application)
        db.refresh(loan)

        return application, loan, repayments

    except Exception:
        db.rollback()
        raise


def get_client_loans(client_id: int, db: Session) -> list[Loan]:
    account_service.get_client_or_404(client_id, db)

    return (
        db.query(Loan)
        .join(LoanApplication)
        .filter(LoanApplication.client_id == client_id)
        .order_by(Loan.loan_id.desc())
        .all()
    )
