from datetime import date

from sqlalchemy import Column, Date, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.enums import ClientType


class Client(Base):
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True)
    client_type = Column(SqlEnum(ClientType), nullable=False)

    phone_number = Column(String(20), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    address = Column(String(255), nullable=False)
    created_at = Column(Date, nullable=False, default=date.today)

    individual_client = relationship(
        "IndividualClient",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan"
    )

    corporate_client = relationship(
        "CorporateClient",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan"
    )

    bank_accounts = relationship(
        "BankAccount",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    loan_applications = relationship(
        "LoanApplication",
        back_populates="client",
        cascade="all, delete-orphan"
    )


class IndividualClient(Base):
    __tablename__ = "individual_clients"

    client_id = Column(
        Integer,
        ForeignKey("clients.client_id"),
        primary_key=True
    )

    egn = Column(String(10), nullable=False, unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=False)

    client = relationship(
        "Client",
        back_populates="individual_client"
    )


class CorporateClient(Base):
    __tablename__ = "corporate_clients"

    client_id = Column(
        Integer,
        ForeignKey("clients.client_id"),
        primary_key=True
    )

    eik = Column(String(20), nullable=False, unique=True)
    name = Column(String(150), nullable=False)

    client = relationship(
        "Client",
        back_populates="corporate_client"
    )