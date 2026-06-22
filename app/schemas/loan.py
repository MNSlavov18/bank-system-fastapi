from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import CreditTypeName, LoanStatus


class MortgageDetailsResponse(BaseModel):
    property_address: str
    property_value: Decimal
    down_payment: Decimal

    model_config = ConfigDict(from_attributes=True)


class LoanResponse(BaseModel):
    loan_id: int
    application_id: int
    client_id: int
    account_id: int
    credit_type_id: int
    credit_type_name: CreditTypeName
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int
    start_date: date
    end_date: date
    status: LoanStatus
    mortgage_details: Optional[MortgageDetailsResponse] = None


class RepaymentInstallmentResponse(BaseModel):
    installment_id: int
    loan_id: int
    installment_number: int
    due_date: date
    installment_amount: Decimal
    principal_part: Decimal
    interest_part: Decimal
    remaining_balance: Decimal
    is_paid: bool


class LoanStatusResponse(BaseModel):
    loan_id: int
    status: LoanStatus
    principal_amount: Decimal
    term_months: int
    total_installments: int
    paid_installments: int
    unpaid_installments: int
    total_paid_amount: Decimal
    remaining_amount: Decimal
    next_due_date: Optional[date] = None