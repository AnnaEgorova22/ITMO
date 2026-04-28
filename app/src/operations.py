import json
from models import MLTask, TaskStatus

from db import SessionLocal
from models import (
    User,
    Balance,
    MLModel,
    MLTask,
    Transaction,
    TransactionType,
    TaskStatus,
    UserRole
)


def create_user(login: str, password: str, role: UserRole = UserRole.user) -> User:
    session = SessionLocal()
    try:
        user = User(login=login, password=password, role=role)
        session.add(user)
        session.flush()

        balance = Balance(user_id=user.id, amount=0.0)
        session.add(balance)

        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def get_all_users():
    session = SessionLocal()
    try:
        return session.query(User).all()
    finally:
        session.close()


def deposit_balance(user_id: int, amount: float) -> None:
    session = SessionLocal()
    try:
        balance = session.query(Balance).filter(Balance.user_id == user_id).first()
        if balance is None:
            raise ValueError("Баланс пользователя не найден")

        balance.amount += amount

        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=TransactionType.top_up
        )
        session.add(transaction)

        session.commit()
    finally:
        session.close()


def withdraw_balance(user_id: int, amount: float) -> None:
    session = SessionLocal()
    try:
        balance = session.query(Balance).filter(Balance.user_id == user_id).first()
        if balance is None:
            raise ValueError("Баланс пользователя не найден")

        if balance.amount < amount:
            raise ValueError("Недостаточно средств на балансе")

        balance.amount -= amount

        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            transaction_type="debit"
        )
        session.add(transaction)

        session.commit()
    finally:
        session.close()


def create_ml_task(user_id: int, model_id: int, input_data: dict) -> MLTask:
    session = SessionLocal()
    try:
        balance = session.query(Balance).filter(Balance.user_id == user_id).first()
        model = session.query(MLModel).filter(MLModel.id == model_id).first()

        if balance is None:
            raise ValueError("Баланс пользователя не найден")
        if model is None:
            raise ValueError("ML-модель не найдена")
        if balance.amount < model.prediction_cost:
            raise ValueError("Недостаточно средств для выполнения предсказания")

        balance.amount -= model.prediction_cost

        task = MLTask(
            user_id=user_id,
            model_id=model_id,
            input_data=json.dumps(input_data, ensure_ascii=False),
            status=TaskStatus.completed,
            prediction_value=0.15
        )
        session.add(task)
        session.flush()

        transaction = Transaction(
            user_id=user_id,
            task_id=task.id,
            amount=model.prediction_cost,
            transaction_type="prediction_charge"
        )
        session.add(transaction)

        session.commit()
        session.refresh(task)
        return task
    finally:
        session.close()


def get_user_task_history(user_id: int):
    session = SessionLocal()
    try:
        return (
            session.query(MLTask)
            .filter(MLTask.user_id == user_id)
            .order_by(MLTask.created_at.desc())
            .all()
        )
    finally:
        session.close()


def get_user_transactions(user_id: int):
    session = SessionLocal()
    try:
        return (
            session.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .all()
        )
    finally:
        session.close()

def get_user_by_id(user_id: int):
    session = SessionLocal()
    try:
        return session.query(User).filter(User.id == user_id).first()
    finally:
        session.close()


def get_user_by_login(login: str):
    session = SessionLocal()
    try:
        return session.query(User).filter(User.login == login).first()
    finally:
        session.close()


def get_user_balance(user_id: int):
    session = SessionLocal()
    try:
        balance = session.query(Balance).filter(Balance.user_id == user_id).first()
        return balance
    finally:
        session.close()

def create_pending_ml_task(user_id: int, model_id: int, input_data: dict) -> MLTask:
    session = SessionLocal()
    try:
        task = MLTask(
            user_id=user_id,
            model_id=model_id,
            input_data=json.dumps(input_data, ensure_ascii=False),
            status=TaskStatus.created,
            prediction_value=None,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    finally:
        session.close()


def complete_ml_task(task_id: int, prediction_value: float, worker_id: str) -> None:
    session = SessionLocal()
    try:
        task = session.query(MLTask).filter(MLTask.id == task_id).first()
        if task is None:
            raise ValueError("ML-задача не найдена")

        task.status = TaskStatus.completed
        task.prediction_value = prediction_value

        session.commit()
    finally:
        session.close()


def fail_ml_task(task_id: int) -> None:
    session = SessionLocal()
    try:
        task = session.query(MLTask).filter(MLTask.id == task_id).first()
        if task is not None:
            task.status = TaskStatus.failed
            session.commit()
    finally:
        session.close()