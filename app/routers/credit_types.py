from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.credit_type import CreditTypeResponse
from app.services import credit_type_service


router = APIRouter(
    prefix="/credit-types",
    tags=["Credit Types"]
)


@router.get("", response_model=list[CreditTypeResponse])
def get_all_credit_types(db: Session = Depends(get_db)):
    return credit_type_service.get_all_credit_types(db)


@router.post("/seed", response_model=list[CreditTypeResponse])
def seed_credit_types(db: Session = Depends(get_db)):
    return credit_type_service.seed_credit_types(db)


@router.get("/{credit_type_id}", response_model=CreditTypeResponse)
def get_credit_type_by_id(
    credit_type_id: int,
    db: Session = Depends(get_db)
):
    return credit_type_service.get_credit_type_by_id(credit_type_id, db)

