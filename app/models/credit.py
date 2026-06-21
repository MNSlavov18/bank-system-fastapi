from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Column, Enum as SqlEnum, Integer, Numeric
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.enums import CreditTypeName


class CreditType(Base):
    __tablename__ = "credit_types"

    credit_type_id = Column(Integer, primary_key=True, index=True)

    type_name = Column(SqlEnum(CreditTypeName), nullable=False, unique=True)
    interest_rate = Column(Numeric(15, 2), nullable=False)
    max_amount = Column(Numeric(15, 2), nullable=False)
    max_term_months = Column(Integer, nullable=False)

    loan_applications = relationship(
        "LoanApplication",
        back_populates="credit_type"
    )

    __table_args__ = (
        CheckConstraint("interest_rate > 0", name="check_interest_rate_positive"),
        CheckConstraint("max_amount > 0", name="check_max_amount_positive"),
        CheckConstraint("max_term_months > 0", name="check_max_term_months_positive"),
    )