from db import SessionLocal
from models import Balance
from operations import (
    create_user,
    get_all_users,
    deposit_balance,
    withdraw_balance,
    create_ml_task,
    get_user_task_history,
    get_user_transactions,
)


def run_tests():
    print("=== Создание пользователя ===")
    user = create_user("test_user_v2", "test123")
    print(f"Создан пользователь: id={user.id}, login={user.login}")

    print("\n=== Получение пользователей ===")
    users = get_all_users()
    for u in users:
        print(u.id, u.login, u.role)

    print("\n=== Пополнение баланса ===")
    deposit_balance(user.id, 50.0)

    session = SessionLocal()
    try:
        balance = session.query(Balance).filter(Balance.user_id == user.id).first()
        print(f"Баланс после пополнения: {balance.amount}")

        print("\n=== Списание баланса ===")
        withdraw_balance(user.id, 20.0)
        session.refresh(balance)
        print(f"Баланс после списания: {balance.amount}")

        print("\n=== Создание ML-задачи ===")
        task = create_ml_task(user.id, 1, {"income": 100000, "age": 35})
        print(f"Создана задача: id={task.id}, prediction={task.prediction_value}")

        print("\n=== История задач пользователя ===")
        tasks = get_user_task_history(user.id)
        for t in tasks:
            print(t.id, t.status, t.prediction_value, t.created_at)

        print("\n=== История транзакций пользователя ===")
        transactions = get_user_transactions(user.id)
        for tr in transactions:
            print(tr.id, tr.transaction_type, tr.amount, tr.created_at)
    finally:
        session.close()


if __name__ == "__main__":
    run_tests()