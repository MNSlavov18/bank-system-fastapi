from datetime import date

from sqlalchemy import CheckConstraint, Column, Date, Enum as SqlEnum, ForeignKey, Integer, Numeric, String

from app.database.database import Base
from app.models.enums import CreditTypeName
from sqlalchemy.orm import relationship

class FailedCredit(Base):
    __tablename__ = "failed_credits"

    failed_credit_id = Column(Integer, primary_key=True, index=True)
    type_name = Column(SqlEnum(CreditTypeName), nullable=False)
    requested_amount = Column(Numeric(15, 2), nullable=False)
    requested_term_months = Column(Integer, nullable=False)
    failure_reason = Column(String(255), nullable=False)
    failed_at = Column(Date, nullable=False, default=date.today)
    account_id = Column(Integer, ForeignKey("bank_accounts.account_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)

    account = relationship(
        "BankAccount",
        backref="failed_credits",
        foreign_keys=[account_id]
    )

    __table_args__ = (
        CheckConstraint("requested_amount > 0", name="check_failed_requested_amount_positive"),
        CheckConstraint("requested_term_months > 0", name="check_failed_requested_term_positive"),
    )