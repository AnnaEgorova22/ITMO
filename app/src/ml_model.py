import os
import joblib
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


MODEL_PATH = "default_risk_model.joblib"


def train_model():
    np.random.seed(42)

    income = np.random.normal(80000, 30000, 1000)
    age = np.random.randint(18, 70, 1000)
    credit_amount = np.random.normal(500000, 200000, 1000)

    X = np.column_stack([income, age, credit_amount])

    y = (
        (income < 60000).astype(int)
        + (age < 25).astype(int)
        + (credit_amount > 600000).astype(int)
    )

    y = (y >= 2).astype(int)

    model = LogisticRegression()
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    return model


def load_model():
    if not os.path.exists(MODEL_PATH):
        return train_model()

    return joblib.load(MODEL_PATH)


def predict_default_probability(features: dict) -> float:
    model = load_model()

    x = np.array([[
        float(features["income"]),
        float(features["age"]),
        float(features["credit_amount"])
    ]])

    probability = model.predict_proba(x)[0][1]
    return round(float(probability), 4)