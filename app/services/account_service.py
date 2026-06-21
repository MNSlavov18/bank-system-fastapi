from decimal import Decimal
import random
import string

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.account import BankAccount
from app.models.client import Client
from app.models.enums import AccountStatus
from app.schemas.account import AccountCreateRequest


def _letters_to_numbers(value: str) -> str:
    result = ""

    for char in value:
        if char.isalpha():
            result += str(ord(char.upper()) - 55)
        else:
            result += char

    return result


def _calculate_iban_check_digits(country_code: str, bban: str) -> str:
    temporary_iban = bban + country_code + "00"
    numeric_iban = _letters_to_numbers(temporary_iban)

    remainder = int(numeric_iban) % 97
    check_digits = 98 - remainder

    return str(check_digits).zfill(2)


def generate_bg_iban(db: Session) -> str:
    """
    Generates a Bulgarian-style IBAN:
    BG + check digits + bank code + branch code + account type + account number

    Example format:
    BG80BNBG96611020345678
    """

    country_code = "BG"
    bank_code = "BNBG"

    while True:
        branch_code = "".join(random.choices(string.digits, k=4))
        account_type = "".join(random.choices(string.digits, k=2))
        account_number = "".join(random.choices(string.digits, k=8))

        bban = bank_code + branch_code + account_type + account_number
        check_digits = _calculate_iban_check_digits(country_code, bban)

        iban = country_code + check_digits + bban

        existing_account = db.query(BankAccount).filter(
            BankAccount.iban == iban
        ).first()

        if not existing_account:
            return iban


def get_client_or_404(client_id: int, db: Session) -> Client:
    client = db.query(Client).filter(
        Client.client_id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found."
        )

    return client


def open_account(data: AccountCreateRequest, db: Session) -> BankAccount:
    get_client_or_404(data.client_id, db)

    account = BankAccount(
        iban=generate_bg_iban(db),
        balance=data.initial_balance,
        status=AccountStatus.ACTIVE,
        client_id=data.client_id
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account

def get_all_accounts(db: Session) -> list[BankAccount]:
    return db.query(BankAccount).order_by(BankAccount.account_id.asc()).all()

def get_accounts_by_client(client_id: int, db: Session) -> list[BankAccount]:
    get_client_or_404(client_id, db)

    return db.query(BankAccount).filter(
        BankAccount.client_id == client_id
    ).order_by(BankAccount.account_id.asc()).all()


def get_account_by_id(account_id: int, client_id: int, db: Session) -> BankAccount:
    account = db.query(BankAccount).filter(
        BankAccount.account_id == account_id,
        BankAccount.client_id == client_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found for this client."
        )

    return account


def close_account(account_id: int, client_id: int, db: Session) -> BankAccount:
    account = get_account_by_id(account_id, client_id, db)

    if account.status == AccountStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already closed."
        )

    if account.balance > Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account cannot be closed while balance is greater than 0."
        )

    account.status = AccountStatus.CLOSED

    db.commit()
    db.refresh(account)

    return account

def add_money_to_account(account_id: int, client_id: int, amount: Decimal, db: Session) -> BankAccount:
    account = get_account_by_id(account_id, client_id, db)
    
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Money can be added only to an active account."
        )

    if amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount to add must be greater than 0."
        )

    account.balance += amount

    db.commit()
    db.refresh(account)

    return account

def draw_money_from_account(account_id: int, client_id: int, amount: Decimal, db: Session) -> BankAccount:
    account = get_account_by_id(account_id, client_id, db)
    
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Money can be drawn only from an active account."
        )

    if amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount to draw must be greater than 0."
        )

    if account.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds in the account."
        )

    account.balance -= amount

    db.commit()
    db.refresh(account)

    return account