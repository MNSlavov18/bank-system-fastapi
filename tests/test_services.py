"""
Comprehensive unit tests for bank system services.
Tests cover account operations, loans, authentication, and validations.
Uses real MySQL database configured in .env for testing.
"""

import pytest
import os
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.database.database import Base
from app.core.config import settings
from app.models.account import BankAccount
from app.models.client import Client, IndividualClient, CorporateClient
from app.models.user import User
from app.models.loan import Loan, LoanApplication
from app.models.credit import CreditType
from app.models.repayment import RepaymentPlan
from app.models.mortgage import MortgageDetails
from app.models.failedCredit import FailedCredit
from app.models.enums import (
    AccountStatus, ClientType, CreditTypeName, LoanStatus, LoanApplicationStatus, LoanDisbursementMethod
)

from app.services import account_service, auth_service, client_service, loan_service, credit_type_service, loan_application_service
from app.schemas.account import AccountCreateRequest
from app.schemas.auth import IndividualRegisterRequest, CorporateRegisterRequest, LoginRequest
from app.schemas.client import ClientUpdateRequest
from app.schemas.loan_application import LoanApplicationCreateRequest

from fastapi import HTTPException


# ============================================================================
# FIXTURES - Database Setup
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """Create a test database session using the configured MySQL database."""
    # Use the database URL from .env configuration
    engine = create_engine(settings.database_url, echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    
    # Cleanup: Drop tables after test to ensure clean state for next test
    # This is more reliable than trying to delete all rows
    connection = engine.raw_connection()
    cursor = connection.cursor()
    try:
        # Disable foreign key checks to allow table drops
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        # Get all table names
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", 
                      (settings.database_url.split('/')[-1],))
        tables = cursor.fetchall()
        # Drop each table
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS `{table[0]}`")
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        connection.commit()
    finally:
        cursor.close()
        connection.close()
    
    engine.dispose()


@pytest.fixture(scope="function")
def seed_credit_types(test_db):
    """Seed default credit types for testing."""
    credit_type_service.seed_credit_types(test_db)
    return test_db


@pytest.fixture(scope="function")
def individual_user(seed_credit_types):
    """Create and return a test individual user with an account."""
    db = seed_credit_types
    
    # Register individual
    register_data = IndividualRegisterRequest(
        email="john@example.com",
        password="testpass123",
        phone_number="359888123456",
        address="Sofia, Bulgaria",
        egn="1234567890",
        first_name="John",
        last_name="Doe",
        birth_date=date(1990, 1, 15)
    )
    auth_service.register_individual(register_data, db)
    
    # Get created user and client
    user = db.query(User).filter(User.email == "john@example.com").first()
    client = user.client
    
    return {"user": user, "client": client, "db": db}


@pytest.fixture(scope="function")
def corporate_user(seed_credit_types):
    """Create and return a test corporate user with an account."""
    db = seed_credit_types
    
    # Register corporate
    register_data = CorporateRegisterRequest(
        email="company@example.com",
        password="testpass123",
        phone_number="359888654321",
        address="Sofia, Bulgaria",
        eik="123456789",
        name="Test Company",
        representative_name="Jane Smith"
    )
    auth_service.register_corporate(register_data, db)
    
    # Get created user and client
    user = db.query(User).filter(User.email == "company@example.com").first()
    client = user.client
    
    return {"user": user, "client": client, "db": db}


@pytest.fixture(scope="function")
def account_with_balance(individual_user):
    """Create an account with initial balance."""
    db = individual_user["db"]
    client = individual_user["client"]
    
    account_data = AccountCreateRequest(
        client_id=client.client_id,
        initial_balance=Decimal("1000.00")
    )
    account = account_service.open_account(account_data, db)
    
    return {"account": account, "client": client, "db": db}


# ============================================================================
# ACCOUNT SERVICE TESTS
# ============================================================================

class TestAccountService:
    """Test account service operations."""
    
    def test_open_account_success(self, individual_user):
        """Test successful account creation."""
        db = individual_user["db"]
        client = individual_user["client"]
        
        account_data = AccountCreateRequest(
            client_id=client.client_id,
            initial_balance=Decimal("500.50")
        )
        account = account_service.open_account(account_data, db)
        
        assert account.account_id is not None
        assert account.balance == Decimal("500.50")
        assert account.status == AccountStatus.ACTIVE
        assert len(account.iban) > 0
        assert account.client_id == client.client_id

    def test_open_account_generates_unique_iban(self, individual_user):
        """Test that each account gets a unique IBAN."""
        db = individual_user["db"]
        client = individual_user["client"]
        
        account_data1 = AccountCreateRequest(
            client_id=client.client_id,
            initial_balance=Decimal("100.00")
        )
        account_data2 = AccountCreateRequest(
            client_id=client.client_id,
            initial_balance=Decimal("200.00")
        )
        
        account1 = account_service.open_account(account_data1, db)
        account2 = account_service.open_account(account_data2, db)
        
        assert account1.iban != account2.iban

    def test_add_money_to_account(self, account_with_balance):
        """Test adding money to an active account."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        initial_balance = account.balance
        amount = Decimal("250.75")
        
        updated_account = account_service.add_money_to_account(
            account.account_id, client.client_id, amount, db
        )
        
        assert updated_account.balance == initial_balance + amount

    def test_add_money_closed_account_fails(self, account_with_balance):
        """Test that money cannot be added to a closed account."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        # Close the account first
        account.status = AccountStatus.CLOSED
        db.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            account_service.add_money_to_account(
                account.account_id, client.client_id, Decimal("100.00"), db
            )
        assert "active account" in str(exc_info.value.detail).lower()

    def test_add_negative_amount_fails(self, account_with_balance):
        """Test that negative amounts cannot be added."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        with pytest.raises(HTTPException) as exc_info:
            account_service.add_money_to_account(
                account.account_id, client.client_id, Decimal("-100.00"), db
            )
        assert "greater than 0" in str(exc_info.value.detail)

    def test_draw_money_from_account(self, account_with_balance):
        """Test drawing money from an active account."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        initial_balance = account.balance
        amount = Decimal("150.00")
        
        updated_account = account_service.draw_money_from_account(
            account.account_id, client.client_id, amount, db
        )
        
        assert updated_account.balance == initial_balance - amount

    def test_draw_insufficient_funds_fails(self, account_with_balance):
        """Test that drawing more than balance fails."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        with pytest.raises(HTTPException) as exc_info:
            account_service.draw_money_from_account(
                account.account_id, client.client_id, Decimal("2000.00"), db
            )
        assert "insufficient" in str(exc_info.value.detail).lower()

    def test_transfer_money_by_iban(self, account_with_balance, individual_user):
        """Test transferring money between accounts by IBAN."""
        db = account_with_balance["db"]
        account1 = account_with_balance["account"]
        client = account_with_balance["client"]
        
        # Create a second account for the recipient
        account_data2 = AccountCreateRequest(
            client_id=client.client_id,
            initial_balance=Decimal("500.00")
        )
        account2 = account_service.open_account(account_data2, db)
        
        amount = Decimal("200.00")
        initial_balance1 = account1.balance
        initial_balance2 = account2.balance
        
        account_service.transfer_money_by_iban(
            account1.account_id, client.client_id, account2.iban, amount, db
        )
        
        db.refresh(account1)
        db.refresh(account2)
        
        assert account1.balance == initial_balance1 - amount
        assert account2.balance == initial_balance2 + amount

    def test_transfer_to_same_account_fails(self, account_with_balance):
        """Test that transferring to the same account fails."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        with pytest.raises(HTTPException) as exc_info:
            account_service.transfer_money_by_iban(
                account.account_id, client.client_id, account.iban, Decimal("100.00"), db
            )
        assert "same account" in str(exc_info.value.detail).lower()

    def test_transfer_to_nonexistent_iban_fails(self, account_with_balance):
        """Test that transferring to non-existent IBAN fails."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        with pytest.raises(HTTPException) as exc_info:
            account_service.transfer_money_by_iban(
                account.account_id, client.client_id, "BG99FAKE1234567890123456", Decimal("100.00"), db
            )
        assert "does not exist" in str(exc_info.value.detail).lower()

    def test_transfer_insufficient_funds_fails(self, account_with_balance, individual_user):
        """Test that transfer with insufficient funds fails."""
        db = account_with_balance["db"]
        account1 = account_with_balance["account"]
        client = account_with_balance["client"]
        
        # Create recipient account
        account_data2 = AccountCreateRequest(
            client_id=client.client_id,
            initial_balance=Decimal("100.00")
        )
        account2 = account_service.open_account(account_data2, db)
        
        with pytest.raises(HTTPException) as exc_info:
            account_service.transfer_money_by_iban(
                account1.account_id, client.client_id, account2.iban, Decimal("2000.00"), db
            )
        assert "insufficient" in str(exc_info.value.detail).lower()

    def test_close_account_success(self, account_with_balance):
        """Test closing an account with zero balance."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        # Draw all money
        account_service.draw_money_from_account(
            account.account_id, client.client_id, account.balance, db
        )
        
        # Close account
        closed_account = account_service.close_account(
            account.account_id, client.client_id, db
        )
        
        assert closed_account.status == AccountStatus.CLOSED

    def test_close_account_with_balance_fails(self, account_with_balance):
        """Test that closing an account with balance fails."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        with pytest.raises(HTTPException) as exc_info:
            account_service.close_account(
                account.account_id, client.client_id, db
            )
        assert "balance is greater than 0" in str(exc_info.value.detail)

    def test_close_already_closed_account_fails(self, account_with_balance):
        """Test that closing an already closed account fails."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        # Close it once
        account_service.draw_money_from_account(
            account.account_id, client.client_id, account.balance, db
        )
        account_service.close_account(account.account_id, client.client_id, db)
        
        # Try to close again
        with pytest.raises(HTTPException) as exc_info:
            account_service.close_account(
                account.account_id, client.client_id, db
            )
        assert "already closed" in str(exc_info.value.detail).lower()

    def test_close_account_with_active_loan_fails(self, account_with_balance, seed_credit_types):
        """Test that closing an account with active loans fails."""
        db = account_with_balance["db"]
        account = account_with_balance["account"]
        client = account_with_balance["client"]
        
        # Create a loan
        credit_type = db.query(CreditType).filter(
            CreditType.type_name == CreditTypeName.CONSUMER
        ).first()
        
        application = LoanApplication(
            requested_amount=Decimal("500.00"),
            requested_term_months=12,
            application_status=LoanApplicationStatus.APPROVED,
            client_id=client.client_id,
            credit_type_id=credit_type.credit_type_id
        )
        db.add(application)
        db.flush()
        
        loan = Loan(
            principal_amount=Decimal("500.00"),
            term_months=12,
            start_date=date.today(),
            end_date=date.today(),
            status=LoanStatus.ACTIVE,
            application_id=application.application_id,
            account_id=account.account_id,
            disbursement_method=LoanDisbursementMethod.CASH
        )
        db.add(loan)
        db.commit()
        
        # Draw all money
        account_service.draw_money_from_account(
            account.account_id, client.client_id, account.balance, db
        )
        
        # Try to close - should fail due to active loan
        with pytest.raises(HTTPException) as exc_info:
            account_service.close_account(
                account.account_id, client.client_id, db
            )
        assert "active loans" in str(exc_info.value.detail).lower()

    def test_get_accounts_by_client(self, account_with_balance):
        """Test retrieving accounts by client."""
        db = account_with_balance["db"]
        client = account_with_balance["client"]
        
        accounts = account_service.get_accounts_by_client(client.client_id, db)
        
        assert len(accounts) >= 1
        assert any(a.account_id == account_with_balance["account"].account_id for a in accounts)


# ============================================================================
# AUTHENTICATION SERVICE TESTS
# ============================================================================

class TestAuthService:
    """Test authentication service operations."""
    
    def test_register_individual_success(self, seed_credit_types):
        """Test successful individual registration."""
        db = seed_credit_types
        
        register_data = IndividualRegisterRequest(
            email="newuser@example.com",
            password="securepass123",
            phone_number="359888999999",
            address="Sofia, Bulgaria",
            egn="9876543210",
            first_name="Jane",
            last_name="Smith",
            birth_date=date(1992, 6, 20)
        )
        
        result = auth_service.register_individual(register_data, db)
        
        user = db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.client.individual_client is not None
        assert user.client.individual_client.egn == "9876543210"

    def test_register_duplicate_email_fails(self, individual_user):
        """Test that registering with duplicate email fails."""
        db = individual_user["db"]
        
        register_data = IndividualRegisterRequest(
            email="john@example.com",
            password="newpass123",
            phone_number="359888777777",
            address="Sophia, Bulgaria",
            egn="1111111111",
            first_name="John",
            last_name="Smith",
            birth_date=date(1995, 1, 1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_individual(register_data, db)
        assert "already exists" in str(exc_info.value.detail).lower()

    def test_register_corporate_success(self, seed_credit_types):
        """Test successful corporate registration."""
        db = seed_credit_types
        
        register_data = CorporateRegisterRequest(
            email="corp@example.com",
            password="corppass123",
            phone_number="359888111111",
            address="Sofia, Bulgaria",
            eik="987654321",
            name="Big Corp",
            representative_name="John Executive"
        )
        
        result = auth_service.register_corporate(register_data, db)
        
        user = db.query(User).filter(User.email == "corp@example.com").first()
        assert user is not None
        assert user.client.corporate_client is not None
        assert user.client.corporate_client.eik == "987654321"

    def test_login_success(self, individual_user):
        """Test successful login."""
        db = individual_user["db"]
        
        login_data = LoginRequest(
            email="john@example.com",
            password="testpass123"
        )
        
        result = auth_service.login(login_data, db)
        
        assert result["user_id"] is not None
        assert result["client_id"] is not None

    def test_login_wrong_password_fails(self, individual_user):
        """Test that login with wrong password fails."""
        db = individual_user["db"]
        
        login_data = LoginRequest(
            email="john@example.com",
            password="wrongpassword"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(login_data, db)
        assert "invalid" in str(exc_info.value.detail).lower()

    def test_login_nonexistent_user_fails(self, seed_credit_types):
        """Test that login with non-existent user fails."""
        db = seed_credit_types
        
        login_data = LoginRequest(
            email="nonexistent@example.com",
            password="anypassword"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(login_data, db)
        assert "invalid" in str(exc_info.value.detail).lower()

    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "mysecretpassword"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert auth_service.verify_password(password, hashed)

    def test_password_verification_fails_with_wrong_password(self):
        """Test that password verification fails with wrong password."""
        password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = auth_service.hash_password(password)
        
        assert not auth_service.verify_password(wrong_password, hashed)


# ============================================================================
# CLIENT SERVICE TESTS
# ============================================================================

class TestClientService:
    """Test client service operations."""
    
    def test_get_client_by_id(self, individual_user):
        """Test getting client by ID."""
        db = individual_user["db"]
        client_id = individual_user["client"].client_id
        
        client = client_service.get_client_by_id(client_id, db)
        
        assert client.client_id == client_id
        assert client.client_type == ClientType.INDIVIDUAL

    def test_get_nonexistent_client_fails(self, seed_credit_types):
        """Test that getting non-existent client fails."""
        db = seed_credit_types
        
        with pytest.raises(HTTPException) as exc_info:
            client_service.get_client_by_id(99999, db)
        assert "not found" in str(exc_info.value.detail).lower()

    def test_update_individual_client(self, individual_user):
        """Test updating individual client details."""
        db = individual_user["db"]
        client = individual_user["client"]
        
        update_data = ClientUpdateRequest(
            email="newemail@example.com",
            phone_number="359888222222",
            address="New Address",
            first_name="Updated",
            last_name="Name",
            name=None,
            representative_name=None
        )
        
        updated_client = client_service.update_client(client.client_id, update_data, db)
        
        assert updated_client.email == "newemail@example.com"
        assert updated_client.phone_number == "359888222222"
        assert updated_client.individual_client.first_name == "Updated"

    def test_update_client_duplicate_email_fails(self, individual_user, corporate_user):
        """Test that updating to duplicate email fails."""
        db = individual_user["db"]
        individual_client = individual_user["client"]
        corporate_client = corporate_user["client"]
        
        # Try to update individual to corporate email
        update_data = ClientUpdateRequest(
            email=corporate_client.email,
            phone_number=None,
            address=None,
            first_name=None,
            last_name=None,
            name=None,
            representative_name=None
        )
        
        with pytest.raises(HTTPException) as exc_info:
            client_service.update_client(individual_client.client_id, update_data, db)
        assert "already exists" in str(exc_info.value.detail).lower()


# ============================================================================
# LOAN SERVICE TESTS
# ============================================================================

class TestLoanService:
    """Test loan service operations."""
    
    def test_get_loans_by_client(self, account_with_balance, seed_credit_types):
        """Test retrieving loans by client."""
        db = account_with_balance["db"]
        client = account_with_balance["client"]
        account = account_with_balance["account"]
        
        # Create a loan
        credit_type = db.query(CreditType).filter(
            CreditType.type_name == CreditTypeName.CONSUMER
        ).first()
        
        application = LoanApplication(
            requested_amount=Decimal("500.00"),
            requested_term_months=12,
            application_status=LoanApplicationStatus.APPROVED,
            client_id=client.client_id,
            credit_type_id=credit_type.credit_type_id
        )
        db.add(application)
        db.flush()
        
        loan = Loan(
            principal_amount=Decimal("500.00"),
            term_months=12,
            start_date=date.today(),
            end_date=date.today(),
            status=LoanStatus.ACTIVE,
            application_id=application.application_id,
            account_id=account.account_id,
            disbursement_method=LoanDisbursementMethod.CASH
        )
        db.add(loan)
        db.commit()
        
        loans = loan_service.get_loans_by_client(client.client_id, db)
        
        assert len(loans) >= 1
        assert any(l["loan_id"] == loan.loan_id for l in loans)

    def test_get_failed_credits_by_client(self, account_with_balance):
        """Test retrieving failed credits by client."""
        db = account_with_balance["db"]
        client = account_with_balance["client"]
        account = account_with_balance["account"]
        
        failed_credit = FailedCredit(
            type_name=CreditTypeName.CONSUMER,
            requested_amount=Decimal("1000.00"),
            requested_term_months=24,
            failure_reason="Insufficient balance",
            failed_at=date.today(),
            account_id=account.account_id,
            client_id=client.client_id
        )
        db.add(failed_credit)
        db.commit()
        
        failed_credits = loan_service.get_failed_credits_by_client(client.client_id, db)
        
        assert len(failed_credits) >= 1
        assert any(f["failed_credit_id"] == failed_credit.failed_credit_id for f in failed_credits)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
