from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.credit import CreditType
from app.models.enums import CreditTypeName
from app.schemas.credit_type import CreditTypeCreateRequest, CreditTypeUpdateRequest


FIXED_CREDIT_TYPES = {
    CreditTypeName.CONSUMER: {
        "interest_rate": Decimal("8.50"),
        "max_amount": Decimal("50000.00"),
        "max_term_months": 84
    },
    CreditTypeName.MORTGAGE: {
        "interest_rate": Decimal("4.20"),
        "max_amount": Decimal("300000.00"),
        "max_term_months": 360
    }
}


def get_all_credit_types(db: Session) -> list[CreditType]:
    return db.query(CreditType).order_by(CreditType.credit_type_id.asc()).all()


def get_credit_type_by_id(credit_type_id: int, db: Session) -> CreditType:
    credit_type = db.query(CreditType).filter(
        CreditType.credit_type_id == credit_type_id
    ).first()

    if not credit_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit type not found."
        )

    return credit_type


def create_credit_type(data: CreditTypeCreateRequest, db: Session) -> CreditType:
    if data.type_name not in FIXED_CREDIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported credit type."
        )

    existing_credit_type = db.query(CreditType).filter(
        CreditType.type_name == data.type_name
    ).first()

    if existing_credit_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credit type already exists."
        )

    credit_type = CreditType(
        type_name=data.type_name,
        interest_rate=data.interest_rate,
        max_amount=data.max_amount,
        max_term_months=data.max_term_months
    )

    db.add(credit_type)
    db.commit()
    db.refresh(credit_type)

    return credit_type


def seed_credit_types(db: Session) -> list[CreditType]:
    for type_name, values in FIXED_CREDIT_TYPES.items():
        existing_credit_type = db.query(CreditType).filter(
            CreditType.type_name == type_name
        ).first()

        if existing_credit_type:
            existing_credit_type.interest_rate = values["interest_rate"]
            existing_credit_type.max_amount = values["max_amount"]
            existing_credit_type.max_term_months = values["max_term_months"]
        else:
            credit_type = CreditType(
                type_name=type_name,
                interest_rate=values["interest_rate"],
                max_amount=values["max_amount"],
                max_term_months=values["max_term_months"]
            )

            db.add(credit_type)

    db.commit()

    return get_all_credit_types(db)


def update_credit_type(
    credit_type_id: int,
    data: CreditTypeUpdateRequest,
    db: Session
) -> CreditType:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Credit types are fixed by bank policy and cannot be edited."
    )
