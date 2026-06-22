from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Column, Date, Enum as SqlEnum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.enums import LoanApplicationStatus, LoanDisbursementMethod, LoanStatus


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    application_id = Column(Integer, primary_key=True, index=True)

    requested_amount = Column(Numeric(15, 2), nullable=False)
    requested_term_months = Column(Integer, nullable=False)
    application_date = Column(Date, nullable=False, default=date.today)
    application_status = Column(
        SqlEnum(LoanApplicationStatus),
        nullable=False,
        default=LoanApplicationStatus.PENDING
    )

    client_id = Column(
        Integer,
        ForeignKey("clients.client_id"),
        nullable=False
    )

    credit_type_id = Column(
        Integer,
        ForeignKey("credit_types.credit_type_id"),
        nullable=False
    )

    client = relationship(
        "Client",
        back_populates="loan_applications"
    )

    credit_type = relationship(
        "CreditType",
        back_populates="loan_applications"
    )

    loan = relationship(
        "Loan",
        back_populates="application",
        uselist=False
    )

    __table_args__ = (
        CheckConstraint("requested_amount > 0", name="check_requested_amount_positive"),
        CheckConstraint("requested_term_months > 0", name="check_requested_term_positive"),
    )


class Loan(Base):
    __tablename__ = "loans"

    loan_id = Column(Integer, primary_key=True, index=True)

    principal_amount = Column(Numeric(15, 2), nullable=False)
    term_months = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SqlEnum(LoanStatus), nullable=False, default=LoanStatus.ACTIVE)

    application_id = Column(
        Integer,
        ForeignKey("loan_applications.application_id"),
        nullable=False,
        unique=True
    )

    # Main account used for credit request checks / down payment / fallback manual payment.
    account_id = Column(
        Integer,
        ForeignKey("bank_accounts.account_id"),
        nullable=False
    )

    disbursement_method = Column(
        SqlEnum(LoanDisbursementMethod),
        nullable=False,
        default=LoanDisbursementMethod.BANK_TRANSFER
    )

    # Account where the loan amount is received when method is BANK_TRANSFER.
    disbursement_account_id = Column(
        Integer,
        ForeignKey("bank_accounts.account_id"),
        nullable=True
    )

    auto_payment_enabled = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # Account used for automatic installments.
    payment_account_id = Column(
        Integer,
        ForeignKey("bank_accounts.account_id"),
        nullable=True
    )

    application = relationship(
        "LoanApplication",
        back_populates="loan"
    )

    account = relationship(
        "BankAccount",
        back_populates="loans",
        foreign_keys=[account_id]
    )

    disbursement_account = relationship(
        "BankAccount",
        foreign_keys=[disbursement_account_id]
    )

    payment_account = relationship(
        "BankAccount",
        foreign_keys=[payment_account_id]
    )

    mortgage_details = relationship(
        "MortgageDetails",
        back_populates="loan",
        uselist=False,
        cascade="all, delete-orphan"
    )

    repayment_plans = relationship(
        "RepaymentPlan",
        back_populates="loan",
        cascade="all, delete-orphan",
        order_by="RepaymentPlan.installment_number"
    )

    __table_args__ = (
        CheckConstraint("principal_amount > 0", name="check_principal_amount_positive"),
        CheckConstraint("term_months > 0", name="check_loan_term_positive"),
    )