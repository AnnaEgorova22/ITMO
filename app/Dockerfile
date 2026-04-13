FROM python:3.11-slim

WORKDIR /app

RUN pip install flask sqlalchemy psycopg2-binary

COPY src/ /app/src/

WORKDIR /app/src

CMD ["python", "main.py"]