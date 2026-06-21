from datetime import date
from pydantic import BaseModel, EmailStr, field_validator


MAX_PASSWORD_BYTES = 72
PASSWORD_TOO_LONG_MESSAGE = (
    "Password is too long. Please use up to 72 English letters, numbers, or symbols."
)


class PasswordValidationMixin(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(PASSWORD_TOO_LONG_MESSAGE)

        return value


class IndividualRegisterRequest(PasswordValidationMixin):
    email: EmailStr
    phone_number: str
    address: str

    egn: str
    first_name: str
    last_name: str
    birth_date: date


class CorporateRegisterRequest(PasswordValidationMixin):
    email: EmailStr
    phone_number: str
    address: str

    eik: str
    name: str
    representative_name: str


class LoginRequest(PasswordValidationMixin):
    email: EmailStr
