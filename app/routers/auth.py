from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.auth import IndividualRegisterRequest, CorporateRegisterRequest, LoginRequest
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/individual")
def register_individual(data: IndividualRegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register_individual(data, db)


@router.post("/register/corporate")
def register_corporate(data: CorporateRegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register_corporate(data, db)


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(data, db)