FROM docker.io/python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock /app

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY . /app

CMD ["python", "/app/run.py"]
