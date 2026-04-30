from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from rabbitmq_client import publish_task

from auth_utils import authenticate_user
from operations import (
    create_user,
    create_pending_ml_task,
    get_user_by_id,
    get_user_by_login,
    get_user_balance,
    deposit_balance,
    create_ml_task,
    get_user_task_history,
    get_user_transactions,
    get_task_by_id,
    get_ml_model_by_id, 
    withdraw_balance, 
    refund_balance_for_task, 
    fail_ml_task
)
from schemas import (
    RegisterRequest,
    LoginRequest,
    BalanceTopUpRequest,
    PredictRequest,
    UserResponse,
    BalanceResponse,
    PredictResponse,
    TransactionResponse,
    TaskResponse,
)

app = FastAPI(title="ML Service API")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui", response_class=HTMLResponse)
def web_interface():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        return file.read()

@app.get("/")
def root():
    return {"message": "ML Service API is running"}


@app.post("/auth/register", response_model=UserResponse)
def register_user(data: RegisterRequest):
    existing_user = get_user_by_login(data.login)
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    user = create_user(data.login, data.password)
    return UserResponse(
        id=user.id,
        login=user.login,
        role=str(user.role.value if hasattr(user.role, "value") else user.role),
    )


@app.post("/auth/login")
def login_user(data: LoginRequest):
    user = authenticate_user(data.login, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    return {
        "message": "Авторизация успешна",
        "user_id": user.id,
        "login": user.login,
    }


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return UserResponse(
        id=user.id,
        login=user.login,
        role=str(user.role.value if hasattr(user.role, "value") else user.role),
    )


@app.get("/balance/{user_id}", response_model=BalanceResponse)
def get_balance(user_id: int):
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    balance = get_user_balance(user_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="Баланс не найден")

    return BalanceResponse(user_id=user_id, balance=balance.amount)


@app.post("/balance/{user_id}/top-up", response_model=BalanceResponse)
def top_up_balance(user_id: int, data: BalanceTopUpRequest):
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    try:
        deposit_balance(user_id, data.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    balance = get_user_balance(user_id)
    return BalanceResponse(user_id=user_id, balance=balance.amount)


@app.post("/predict", response_model=PredictResponse)
def predict(data: PredictRequest):
    user = get_user_by_id(data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    try:
        task = create_ml_task(
            user_id=data.user_id,
            model_id=data.model_id,
            input_data=data.input_data,
        )
    except ValueError as e:
        message = str(e)
        if "Недостаточно средств" in message:
            raise HTTPException(status_code=400, detail=message)
        raise HTTPException(status_code=400, detail=message)

    return PredictResponse(
        task_id=task.id,
        status=str(task.status.value if hasattr(task.status, "value") else task.status),
        prediction_value=task.prediction_value,
    )


@app.get("/history/{user_id}/tasks", response_model=list[TaskResponse])
def get_task_history(user_id: int):
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    tasks = get_user_task_history(user_id)
    return [
        TaskResponse(
            id=task.id,
            status=str(task.status.value if hasattr(task.status, "value") else task.status),
            prediction_value=task.prediction_value,
            created_at=task.created_at,
        )
        for task in tasks
    ]


@app.get("/history/{user_id}/transactions", response_model=list[TransactionResponse])
def get_transaction_history(user_id: int):
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    transactions = get_user_transactions(user_id)
    return [
        TransactionResponse(
            id=tr.id,
            amount=tr.amount,
            transaction_type=str(
                tr.transaction_type.value if hasattr(tr.transaction_type, "value") else tr.transaction_type
            ),
            created_at=tr.created_at,
        )
        for tr in transactions
    ]

@app.post("/predict-async")
def predict_async(data: PredictRequest):
    user = get_user_by_id(data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    balance = get_user_balance(data.user_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="Баланс не найден")

    ml_model = get_ml_model_by_id(data.model_id)
    if ml_model is None:
        raise HTTPException(status_code=404, detail="ML-модель не найдена")

    if balance.amount <= 0:
        raise HTTPException(status_code=400, detail="Баланс должен быть положительным")

    if balance.amount < ml_model.prediction_cost:
        raise HTTPException(status_code=400, detail="Недостаточно средств для выполнения предсказания")

    task = create_pending_ml_task(
        user_id=data.user_id,
        model_id=data.model_id,
        input_data=data.input_data,
    )

    try:
        withdraw_balance(
            user_id=data.user_id,
            amount=ml_model.prediction_cost,
        )

        message = {
            "task_id": task.id,
            "features": data.input_data,
            "model": ml_model.name,
            "status": "created",
        }

        publish_task(message)

    except Exception as error:
        fail_ml_task(task.id)

        try:
            refund_balance_for_task(task.id)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при постановке задачи в очередь: {error}"
        )

    return {
        "task_id": task.id,
        "status": "created",
        "message": "Задача отправлена в очередь RabbitMQ",
    }

@app.get("/tasks/{task_id}")
def get_task_result(task_id: int):
    task = get_task_by_id(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="ML-задача не найдена")

    return {
        "task_id": task.id,
        "user_id": task.user_id,
        "model_id": task.model_id,
        "status": task.status.value if hasattr(task.status, "value") else task.status,
        "prediction_value": task.prediction_value,
        "created_at": task.created_at,
    }