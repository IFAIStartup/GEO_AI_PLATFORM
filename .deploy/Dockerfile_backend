FROM python:3.9.13-slim-buster
WORKDIR /geo_ai_backend
RUN apt-get update && apt-get install -y libpq-dev gcc ffmpeg libsm6 libxext6 libkrb5-dev python3-dev
RUN pip install --upgrade pip
RUN pip install poetry==1.5.1
COPY poetry.lock pyproject.toml /geo_ai_backend/
RUN poetry config virtualenvs.create false && poetry install --only main --no-interaction --no-ansi
COPY ./ /geo_ai_backend
