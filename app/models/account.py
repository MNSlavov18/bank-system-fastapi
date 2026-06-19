from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, Date, Enum as SqlEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.enums import AccountStatus


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    account_id = Column(Integer, primary_key=True, index=True)

    iban = Column(String(34), nullable=False, unique=True)
    balance = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    status = Column(SqlEnum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE)
    opened_at = Column(Date, nullable=False, default=date.today)

    client_id = Column(
        Integer,
        ForeignKey("clients.client_id"),
        nullable=False
    )

    client = relationship(
        "Client",
        back_populates="bank_accounts"
    )

    loans = relationship(
        "Loan",
        back_populates="account"
    )

    __table_args__ = (
        CheckConstraint("balance >= 0", name="check_account_balance_positive"),
    )