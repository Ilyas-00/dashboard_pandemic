FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --shell /bin/bash etl_user

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements depuis le même dossier
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl_main.py .
COPY data_cleaner.py .
COPY db_config.py .

RUN chown -R etl_user:etl_user /app
USER etl_user

CMD ["python3", "etl_main.py"]
