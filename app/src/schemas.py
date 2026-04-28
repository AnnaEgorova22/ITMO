from datetime import datetime
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    login: str = Field(..., min_length=3)
    password: str = Field(..., min_length=3)

class LoginRequest(BaseModel):
    login: str
    password: str


class BalanceTopUpRequest(BaseModel):
    amount: float = Field(..., gt=0)


class PredictRequest(BaseModel):
    user_id: int
    model_id: int
    input_data: dict


class UserResponse(BaseModel):
    id: int
    login: str
    role: str


class BalanceResponse(BaseModel):
    user_id: int
    balance: float


class PredictResponse(BaseModel):
    task_id: int
    status: str
    prediction_value: float


class TransactionResponse(BaseModel):
    id: int
    amount: float
    transaction_type: str
    created_at: datetime


class TaskResponse(BaseModel):
    id: int
    status: str
    prediction_value: float | None
    created_at: datetime