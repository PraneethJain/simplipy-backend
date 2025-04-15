FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y curl build-essential && \
    rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.0.1
RUN curl -sSL https://install.python-poetry.org | python - --version $POETRY_VERSION

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "simplipy.main:app", "--host", "0.0.0.0", "--port", "8080"]
