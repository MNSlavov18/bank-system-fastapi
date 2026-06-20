from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountStatus


class AccountCreateRequest(BaseModel):
    client_id: int = Field(..., gt=0)
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)


class AccountResponse(BaseModel):
    account_id: int
    iban: str
    balance: Decimal
    status: AccountStatus
    opened_at: date
    client_id: int

    model_config = ConfigDict(from_attributes=True)