import json
import os
import time
import pika

from operations import complete_ml_task, fail_ml_task


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "ml_tasks")
WORKER_ID = os.getenv("WORKER_ID", "worker-unknown")


def validate_features(features: dict) -> None:
    if not isinstance(features, dict):
        raise ValueError("features должны быть JSON-объектом")

    if "income" not in features:
        raise ValueError("Отсутствует обязательное поле income")

    if "age" not in features:
        raise ValueError("Отсутствует обязательное поле age")


def make_prediction(features: dict) -> float:
    income = float(features.get("income", 0))
    age = float(features.get("age", 0))

    prediction = 0.15

    if income < 50000:
        prediction += 0.10

    if age < 25:
        prediction += 0.05

    return round(prediction, 4)


def process_message(ch, method, properties, body):
    try:
        message = json.loads(body.decode("utf-8"))

        task_id = message["task_id"]
        features = message["features"]

        print(f"[{WORKER_ID}] Получена задача task_id={task_id}", flush=True)

        validate_features(features)

        time.sleep(2)

        prediction = make_prediction(features)

        complete_ml_task(
            task_id=task_id,
            prediction_value=prediction,
            worker_id=WORKER_ID,
        )

        print(
            f"[{WORKER_ID}] Задача обработана: "
            f"task_id={task_id}, prediction={prediction}, status=completed", flush=True
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as error:
        print(f"[{WORKER_ID}] Ошибка обработки задачи: {error}", flush=True)

        try:
            if "task_id" in locals():
                fail_ml_task(task_id)
        except Exception as db_error:
            print(f"[{WORKER_ID}] Ошибка обновления статуса задачи: {db_error}", flush=True)

        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                )
            )
            channel = connection.channel()

            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=RABBITMQ_QUEUE,
                on_message_callback=process_message,
            )

            print(f"[{WORKER_ID}] Worker запущен и слушает очередь {RABBITMQ_QUEUE}", flush=True)
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            print(f"[{WORKER_ID}] RabbitMQ недоступен, повторное подключение через 5 секунд", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()