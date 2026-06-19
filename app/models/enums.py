from enum import Enum


class ClientType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    CORPORATE = "CORPORATE"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class LoanApplicationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LoanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CLOSED = "CLOSED"


class CreditTypeName(str, Enum):
    CONSUMER = "CONSUMER"
    MORTGAGE = "MORTGAGE"