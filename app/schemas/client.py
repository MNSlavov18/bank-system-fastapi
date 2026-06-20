from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import ClientType


class IndividualClientResponse(BaseModel):
    egn: str
    first_name: str
    last_name: str
    birth_date: date

    model_config = ConfigDict(from_attributes=True)


class CorporateClientResponse(BaseModel):
    eik: str
    name: str
    representative_name: str

    model_config = ConfigDict(from_attributes=True)


class ClientResponse(BaseModel):
    client_id: int
    client_type: ClientType
    phone_number: str
    email: EmailStr
    address: str
    created_at: date

    individual_client: Optional[IndividualClientResponse] = None
    corporate_client: Optional[CorporateClientResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ClientUpdateRequest(BaseModel):
    phone_number: Optional[str] = Field(default=None, min_length=5, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(default=None, min_length=3, max_length=255)

    # Only for individual clients
    first_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=2, max_length=100)

    # Only for corporate clients
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    representative_name: Optional[str] = Field(default=None, min_length=2, max_length=200)


class MessageResponse(BaseModel):
    message: str