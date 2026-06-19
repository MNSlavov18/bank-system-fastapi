from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class MortgageDetails(Base):
    __tablename__ = "mortgage_details"

    loan_id = Column(
        Integer,
        ForeignKey("loans.loan_id"),
        primary_key=True
    )

    property_address = Column(String(255), nullable=False)
    property_value = Column(Numeric(15, 2), nullable=False)
    down_payment = Column(Numeric(15, 2), nullable=False)

    loan = relationship(
        "Loan",
        back_populates="mortgage_details"
    )

    __table_args__ = (
        CheckConstraint("property_value > 0", name="check_property_value_positive"),
        CheckConstraint("down_payment >= 0", name="check_down_payment_not_negative"),
    )