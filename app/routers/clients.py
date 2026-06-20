from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.client import ClientResponse, ClientUpdateRequest, MessageResponse
from app.services import client_service


router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)


@router.get("", response_model=list[ClientResponse])
def get_all_clients(db: Session = Depends(get_db)):
    return client_service.get_all_clients(db)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client_by_id(
    client_id: int,
    db: Session = Depends(get_db)
):
    return client_service.get_client_by_id(client_id, db)


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    data: ClientUpdateRequest,
    db: Session = Depends(get_db)
):
    return client_service.update_client(client_id, data, db)


@router.delete("/{client_id}", response_model=MessageResponse)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db)
):
    return client_service.delete_client(client_id, db)