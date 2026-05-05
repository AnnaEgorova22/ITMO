from db import SessionLocal
from models import User


def authenticate_user(login: str, password: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.login == login).first()
        if user is None:
            return None
        if user.password != password:
            return None
        return user
    finally:
        session.close()