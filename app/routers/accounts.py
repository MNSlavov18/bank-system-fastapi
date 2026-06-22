from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.account import AccountCreateRequest, AccountResponse
from app.services import account_service


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
)


@router.get("", response_model=list[AccountResponse])
def get_all_accounts(db: Session = Depends(get_db)):
    return account_service.get_all_accounts(db)


@router.post("/open", response_model=AccountResponse)
def open_account(
    data: AccountCreateRequest,
    db: Session = Depends(get_db)
):
    return account_service.open_account(data, db)


@router.get("/client/{client_id}", response_model=list[AccountResponse])
def get_accounts_by_client(
    client_id: int,
    db: Session = Depends(get_db)
):
    return account_service.get_accounts_by_client(client_id, db)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account_by_id(
    account_id: int,
    client_id: int = Query(...),
    db: Session = Depends(get_db)
):
    return account_service.get_account_by_id(account_id, client_id, db)


@router.patch("/{account_id}/close", response_model=AccountResponse)
def close_account(
    account_id: int,
    client_id: int = Query(...),
    db: Session = Depends(get_db)
):
    return account_service.close_account(account_id, client_id, db)

@router.patch("/{account_id}/add-money", response_model=AccountResponse)
def add_money_to_account(
    account_id: int,
    amount: float = Query(..., gt=0),
    client_id: int = Query(...),
    db: Session = Depends(get_db)
):
    return account_service.add_money_to_account(account_id, client_id, amount, db)

@router.patch("/{account_id}/remove-money", response_model=AccountResponse)
def remove_money_from_account(
    account_id: int,
    amount: float = Query(..., gt=0),
    client_id: int = Query(...),
    db: Session = Depends(get_db)
):
    return account_service.draw_money_from_account(account_id, amount, client_id, db)