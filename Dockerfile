FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PRACTICE_HOME=/data

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home --home-dir /home/app app

COPY pyproject.toml ./
COPY app ./app
COPY statements ./statements
COPY 9021 ./9021
COPY README.md ./README.md

RUN pip install --upgrade pip && pip install .

RUN mkdir -p /data /app/statements \
    && chown -R app:app /app /data

USER app

EXPOSE 8000

CMD ["python", "-m", "app.web"]
