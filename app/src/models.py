from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy import Enum

from db import Base

import enum

class TaskStatus(enum.Enum):
    created = "created"
    completed = "completed"
    failed = "failed"


class TransactionType(enum.Enum):
    refund = "refund"
    top_up = "top_up"
    debit = "debit"
    prediction_charge = "prediction_charge"


class UserRole(enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    balance = relationship("Balance", back_populates="user", uselist=False)
    tasks = relationship("MLTask", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")


class Balance(Base):
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)

    user = relationship("User", back_populates="balance")


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    prediction_cost = Column(Float, nullable=False)

    tasks = relationship("MLTask", back_populates="model")


class MLTask(Base):
    __tablename__ = "ml_tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    input_data = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), nullable=False)
    prediction_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tasks")
    model = relationship("MLModel", back_populates="tasks")
    transactions = relationship("Transaction", back_populates="task")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("ml_tasks.id"), nullable=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    task = relationship("MLTask", back_populates="transactions")