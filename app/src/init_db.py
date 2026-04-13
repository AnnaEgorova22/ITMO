from db import engine, SessionLocal, Base
from models import User, Balance, MLModel


def init_database():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        demo_user = session.query(User).filter(User.login == "demo_user").first()
        if demo_user is None:
            demo_user = User(login="demo_user", password="demo123", role="user")
            session.add(demo_user)
            session.flush()

            balance = Balance(user_id=demo_user.id, amount=100.0)
            session.add(balance)

        model_1 = session.query(MLModel).filter(MLModel.name == "Default Risk Model").first()
        if model_1 is None:
            session.add(
                MLModel(
                    name="Default Risk Model",
                    description="Модель оценки вероятности дефолта",
                    prediction_cost=10.0
                )
            )

        model_2 = session.query(MLModel).filter(MLModel.name == "Scoring Model").first()
        if model_2 is None:
            session.add(
                MLModel(
                    name="Scoring Model",
                    description="Скоринговая модель для оценки заемщика",
                    prediction_cost=5.0
                )
            )

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    init_database()