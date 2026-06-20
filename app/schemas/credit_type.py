from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CreditTypeName


class CreditTypeCreateRequest(BaseModel):
    type_name: CreditTypeName
    interest_rate: Decimal = Field(..., gt=0)
    max_amount: Decimal = Field(..., gt=0)
    max_term_months: int = Field(..., gt=0)


class CreditTypeUpdateRequest(BaseModel):
    interest_rate: Optional[Decimal] = Field(default=None, gt=0)
    max_amount: Optional[Decimal] = Field(default=None, gt=0)
    max_term_months: Optional[int] = Field(default=None, gt=0)


class CreditTypeResponse(BaseModel):
    credit_type_id: int
    type_name: CreditTypeName
    interest_rate: Decimal
    max_amount: Decimal
    max_term_months: int

    model_config = ConfigDict(from_attributes=True)