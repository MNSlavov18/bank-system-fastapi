from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.enums import ClientType
from app.models.user import User
from app.schemas.client import ClientUpdateRequest


def get_all_clients(db: Session) -> list[Client]:
    return db.query(Client).order_by(Client.client_id.asc()).all()


def get_client_by_id(client_id: int, db: Session) -> Client:
    client = db.query(Client).filter(Client.client_id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found."
        )

    return client


def update_client(client_id: int, data: ClientUpdateRequest, db: Session) -> Client:
    client = get_client_by_id(client_id, db)

    if data.email is not None and data.email != client.email:
        existing_client = db.query(Client).filter(Client.email == data.email).first()

        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client with this email already exists."
            )

        user = db.query(User).filter(User.client_id == client.client_id).first()

        if user:
            user.email = data.email

        client.email = data.email

    if data.phone_number is not None and data.phone_number != client.phone_number:
        existing_client = db.query(Client).filter(
            Client.phone_number == data.phone_number
        ).first()

        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client with this phone number already exists."
            )

        client.phone_number = data.phone_number

    if data.address is not None:
        client.address = data.address

    if client.client_type == ClientType.INDIVIDUAL:
        if data.name is not None or data.representative_name is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corporate fields cannot be updated for an individual client."
            )

        if data.first_name is not None:
            client.individual_client.first_name = data.first_name

        if data.last_name is not None:
            client.individual_client.last_name = data.last_name

    elif client.client_type == ClientType.CORPORATE:
        if data.first_name is not None or data.last_name is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Individual fields cannot be updated for a corporate client."
            )

        if data.name is not None:
            client.corporate_client.name = data.name

        if data.representative_name is not None:
            client.corporate_client.representative_name = data.representative_name

    db.commit()
    db.refresh(client)

    return client


def delete_client(client_id: int, db: Session) -> dict:
    client = get_client_by_id(client_id, db)

    if client.bank_accounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client cannot be deleted because they have bank accounts."
        )

    if client.loan_applications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client cannot be deleted because they have loan applications."
        )

    user = db.query(User).filter(User.client_id == client.client_id).first()

    if user:
        db.delete(user)

    db.delete(client)
    db.commit()

    return {"message": "Client deleted successfully."}