from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, Boolean,
    DateTime, Date, ForeignKey, Text, Enum as SAEnum, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class AccountType(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    CRYPTO = "crypto"
    SAVINGS = "savings"
    INVESTMENT = "investment"


class DebtType(str, enum.Enum):
    I_OWE = "i_owe"           # I owe someone
    OWE_ME = "owe_me"         # Someone owes me
    CREDIT = "credit"         # Bank credit
    MORTGAGE = "mortgage"     # Mortgage
    INSTALLMENT = "installment"  # Installment


class DebtStatus(str, enum.Enum):
    ACTIVE = "active"
    PAID = "paid"
    OVERDUE = "overdue"


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Currency(str, enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    USDT = "USDT"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    language = Column(String(10), default="ru")
    default_currency = Column(SAEnum(Currency), default=Currency.RUB)
    pin_hash = Column(String(255), nullable=True)
    is_premium = Column(Boolean, default=False)
    timezone = Column(String(50), default="Europe/Moscow")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    debts = relationship("Debt", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    account_type = Column(SAEnum(AccountType), nullable=False)
    currency = Column(SAEnum(Currency), default=Currency.RUB)
    balance = Column(Numeric(15, 2), default=0)
    icon = Column(String(10), default="💳")
    color = Column(String(7), default="#3B82F6")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(10), default="📦")
    color = Column(String(7), default="#6B7280")
    transaction_type = Column(SAEnum(TransactionType), nullable=False)
    is_system = Column(Boolean, default=False)
    budget_limit = Column(Numeric(15, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transactions_user_date", "user_id", "date"),
        Index("idx_transactions_user_type", "user_id", "transaction_type"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    transaction_type = Column(SAEnum(TransactionType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(SAEnum(Currency), default=Currency.RUB)
    description = Column(Text, nullable=True)
    date = Column(Date, default=date.today)
    is_recurring = Column(Boolean, default=False)
    recurring_period = Column(String(20), nullable=True)  # daily, weekly, monthly, yearly
    receipt_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    debt_type = Column(SAEnum(DebtType), nullable=False)
    title = Column(String(200), nullable=False)
    person_name = Column(String(200), nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(SAEnum(Currency), default=Currency.RUB)
    interest_rate = Column(Numeric(5, 2), default=0)
    monthly_payment = Column(Numeric(15, 2), nullable=True)
    start_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(SAEnum(DebtStatus), default=DebtStatus.ACTIVE)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="debts")
    payments = relationship("DebtPayment", back_populates="debt", cascade="all, delete-orphan")


class DebtPayment(Base):
    __tablename__ = "debt_payments"

    id = Column(Integer, primary_key=True)
    debt_id = Column(Integer, ForeignKey("debts.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, default=date.today)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    debt = relationship("Debt", back_populates="payments")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), default=0)
    currency = Column(SAEnum(Currency), default=Currency.RUB)
    deadline = Column(Date, nullable=True)
    icon = Column(String(10), default="🎯")
    status = Column(SAEnum(GoalStatus), default=GoalStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="goals")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    period = Column(String(20), default="monthly")  # monthly, weekly
    currency = Column(SAEnum(Currency), default=Currency.RUB)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="budgets")
    category = relationship("Category")
