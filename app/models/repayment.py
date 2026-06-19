from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.database import Base


class RepaymentPlan(Base):
    __tablename__ = "repayment_plans"

    installment_id = Column(Integer, primary_key=True, index=True)

    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)

    principal_part = Column(Numeric(15, 2), nullable=False)
    interest_part = Column(Numeric(15, 2), nullable=False)
    remaining_balance = Column(Numeric(15, 2), nullable=False)

    is_paid = Column(Boolean, nullable=False, default=False)

    loan_id = Column(
        Integer,
        ForeignKey("loans.loan_id"),
        nullable=False
    )

    loan = relationship(
        "Loan",
        back_populates="repayment_plans"
    )

    __table_args__ = (
        UniqueConstraint(
            "loan_id",
            "installment_number",
            name="uq_loan_installment_number"
        ),
        CheckConstraint("installment_number > 0", name="check_installment_number_positive"),
        CheckConstraint("principal_part >= 0", name="check_principal_part_not_negative"),
        CheckConstraint("interest_part >= 0", name="check_interest_part_not_negative"),
        CheckConstraint("remaining_balance >= 0", name="check_remaining_balance_not_negative"),
    )