from fastapi import HTTPException, status
import bcrypt
from sqlalchemy.orm import Session

from app.models.client import Client, IndividualClient, CorporateClient
from app.models.user import User
from app.models.enums import ClientType
from app.schemas.auth import IndividualRegisterRequest, CorporateRegisterRequest, LoginRequest


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    return password_hash.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def register_individual(data: IndividualRegisterRequest, db: Session):
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    client = Client(
        client_type=ClientType.INDIVIDUAL,
        phone_number=data.phone_number,
        email=data.email,
        address=data.address
    )

    db.add(client)
    db.flush()

    individual_client = IndividualClient(
        client_id=client.client_id,
        egn=data.egn,
        first_name=data.first_name,
        last_name=data.last_name,
        birth_date=data.birth_date
    )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        client_id=client.client_id
    )

    db.add(individual_client)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Individual account created successfully."}


def register_corporate(data: CorporateRegisterRequest, db: Session):
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    client = Client(
        client_type=ClientType.CORPORATE,
        phone_number=data.phone_number,
        email=data.email,
        address=data.address
    )

    db.add(client)
    db.flush()

    corporate_client = CorporateClient(
        client_id=client.client_id,
        eik=data.eik,
        name=data.name,
        representative_name=data.representative_name
    )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        client_id=client.client_id
    )

    db.add(corporate_client)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Corporate account created successfully."}


def login(data: LoginRequest, db: Session):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    return {
        "message": "Login successful.",
        "user_id": user.user_id,
        "client_id": user.client_id
    }
