from datetime import date
from pydantic import BaseModel, EmailStr, field_validator


MAX_PASSWORD_BYTES = 72
MIN_PASSWORD_LENGTH = 5
PASSWORD_TOO_LONG_MESSAGE = (
    "Password is too long. Please use up to 72 English letters, numbers, or symbols."
)
PASSWORD_TOO_SHORT_MESSAGE = "Password must be at least 5 characters long."


class PasswordValidationMixin(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(PASSWORD_TOO_LONG_MESSAGE)

        return value


class RegisterPasswordValidationMixin(PasswordValidationMixin):
    @field_validator("password")
    @classmethod
    def validate_password_min_length(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(PASSWORD_TOO_SHORT_MESSAGE)

        return value


class IndividualRegisterRequest(RegisterPasswordValidationMixin):
    email: EmailStr
    phone_number: str
    address: str

    egn: str
    first_name: str
    last_name: str
    birth_date: date


class CorporateRegisterRequest(RegisterPasswordValidationMixin):
    email: EmailStr
    phone_number: str
    address: str

    eik: str
    name: str
    representative_name: str


class LoginRequest(PasswordValidationMixin):
    email: EmailStr
