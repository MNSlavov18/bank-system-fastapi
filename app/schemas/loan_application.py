from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import LoanApplicationStatus, LoanDisbursementMethod, LoanStatus


class LoanApplicationCreateRequest(BaseModel):
    account_id: int = Field(..., gt=0)
    credit_type_id: int = Field(..., gt=0)
    requested_amount: Decimal = Field(..., gt=0)
    requested_term_months: int = Field(..., gt=0)

    disbursement_method: LoanDisbursementMethod = LoanDisbursementMethod.BANK_TRANSFER
    disbursement_account_id: Optional[int] = Field(default=None, gt=0)

    auto_payment_enabled: bool = False
    payment_account_id: Optional[int] = Field(default=None, gt=0)

    property_address: Optional[str] = None
    property_value: Optional[Decimal] = Field(default=None, gt=0)
    down_payment: Optional[Decimal] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def normalize_blank_fields(self):
        if self.property_address is not None and not self.property_address.strip():
            self.property_address = None

        return self


class LoanApplicationResponse(BaseModel):
    application_id: int
    requested_amount: Decimal
    requested_term_months: int
    application_date: date
    application_status: LoanApplicationStatus
    client_id: int
    credit_type_id: int

    model_config = ConfigDict(from_attributes=True)


class LoanCreatedResponse(BaseModel):
    application_id: int
    loan_id: int
    account_id: int
    application_status: LoanApplicationStatus
    loan_status: LoanStatus
    principal_amount: Decimal
    term_months: int
    start_date: date
    end_date: date
    installments_created: int

    disbursement_method: LoanDisbursementMethod
    disbursement_account_id: Optional[int] = None
    auto_payment_enabled: bool
    payment_account_id: Optional[int] = None


class ClientLoanSummaryResponse(BaseModel):
    application_id: int
    loan_id: int
    account_id: int
    credit_type: str
    principal_amount: Decimal
    term_months: int
    loan_status: LoanStatus
    start_date: date
    end_date: date

    disbursement_method: LoanDisbursementMethod
    disbursement_account_id: Optional[int] = None
    auto_payment_enabled: bool
    payment_account_id: Optional[int] = None