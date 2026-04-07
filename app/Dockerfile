FROM python:3.11-slim

WORKDIR /app

RUN pip install flask

COPY src/ /app/src/

WORKDIR /app/src

CMD ["python", "main.py"]