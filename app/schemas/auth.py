from datetime import date
from pydantic import BaseModel, EmailStr


class IndividualRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: str
    address: str

    egn: str
    first_name: str
    last_name: str
    birth_date: date


class CorporateRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: str
    address: str

    eik: str
    name: str
    representative_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str