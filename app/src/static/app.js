let currentUserId = null;
let currentLogin = null;

function showMessage(message) {
    document.getElementById("message-box").textContent =
        typeof message === "string" ? message : JSON.stringify(message, null, 2);
}

async function handleResponse(response) {
    const text = await response.text();

    let data;
    try {
        data = JSON.parse(text);
    } catch {
        data = text;
    }

    if (!response.ok) {
        throw data;
    }

    return data;
}

async function registerUser() {
    const login = document.getElementById("register-login").value;
    const password = document.getElementById("register-password").value;

    try {
        const response = await fetch("/auth/register", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({login, password})
        });

        const data = await handleResponse(response);
        showMessage(data);
    } catch (error) {
        showMessage(error);
    }
}

async function loginUser() {
    const login = document.getElementById("login-login").value;
    const password = document.getElementById("login-password").value;

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({login, password})
        });

        const data = await handleResponse(response);

        currentUserId = data.user_id;
        currentLogin = data.login;

        document.getElementById("current-user-id").textContent = currentUserId;
        document.getElementById("current-login").textContent = currentLogin;

        showMessage(data);
        await loadBalance();
    } catch (error) {
        showMessage(error);
    }
}

async function loadBalance() {
    if (!currentUserId) {
        showMessage("Сначала выполните авторизацию");
        return;
    }

    try {
        const response = await fetch(`/balance/${currentUserId}`);
        const data = await handleResponse(response);

        document.getElementById("current-balance").textContent = data.balance;
        showMessage(data);
    } catch (error) {
        showMessage(error);
    }
}

async function topUpBalance() {
    if (!currentUserId) {
        showMessage("Сначала выполните авторизацию");
        return;
    }

    const amount = Number(document.getElementById("topup-amount").value);

    try {
        const response = await fetch(`/balance/${currentUserId}/top-up`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({amount})
        });

        const data = await handleResponse(response);

        document.getElementById("current-balance").textContent = data.balance;
        showMessage(data);
    } catch (error) {
        showMessage(error);
    }
}

async function makePrediction() {
    if (!currentUserId) {
        showMessage("Сначала выполните авторизацию");
        return;
    }

    const modelId = Number(document.getElementById("model-id").value);
    const income = Number(document.getElementById("income").value);
    const age = Number(document.getElementById("age").value);
    const creditAmount = Number(document.getElementById("credit-amount").value);

    const payload = {
        user_id: currentUserId,
        model_id: modelId,
        input_data: {
            income: income,
            age: age,
            credit_amount: creditAmount
        }
    };

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        const data = await handleResponse(response);

        document.getElementById("prediction-result").textContent =
            JSON.stringify(data, null, 2);

        showMessage(data);
        await loadBalance();
        await loadTaskHistory();
        await loadTransactionHistory();
    } catch (error) {
        document.getElementById("prediction-result").textContent =
            JSON.stringify(error, null, 2);
        showMessage(error);
    }
}

async function loadTaskHistory() {
    if (!currentUserId) {
        showMessage("Сначала выполните авторизацию");
        return;
    }

    try {
        const response = await fetch(`/history/${currentUserId}/tasks`);
        const data = await handleResponse(response);

        const container = document.getElementById("task-history");
        container.innerHTML = "";

        data.forEach(task => {
            const item = document.createElement("div");
            item.className = "history-item";
            item.innerHTML = `
                <b>ID задачи:</b> ${task.id}<br>
                <b>Статус:</b> ${task.status}<br>
                <b>Предсказание:</b> ${task.prediction_value}<br>
                <b>Дата:</b> ${task.created_at}
            `;
            container.appendChild(item);
        });

        showMessage(data);
    } catch (error) {
        showMessage(error);
    }
}

async function loadTransactionHistory() {
    if (!currentUserId) {
        showMessage("Сначала выполните авторизацию");
        return;
    }

    try {
        const response = await fetch(`/history/${currentUserId}/transactions`);
        const data = await handleResponse(response);

        const container = document.getElementById("transaction-history");
        container.innerHTML = "";

        data.forEach(transaction => {
            const item = document.createElement("div");
            item.className = "history-item";
            item.innerHTML = `
                <b>ID транзакции:</b> ${transaction.id}<br>
                <b>Тип:</b> ${transaction.transaction_type}<br>
                <b>Сумма:</b> ${transaction.amount}<br>
                <b>Дата:</b> ${transaction.created_at}
            `;
            container.appendChild(item);
        });

        showMessage(data);
    } catch (error) {
        showMessage(error);
    }
}