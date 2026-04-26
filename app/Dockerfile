FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn flask sqlalchemy psycopg2-binary

COPY src/ /app/src/

WORKDIR /app/src

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

