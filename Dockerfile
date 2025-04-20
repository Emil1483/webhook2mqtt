FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml .
COPY poetry.lock .
COPY README.md .
RUN poetry install

COPY . .

CMD ["poetry",  "run", "python", "main.py"]
