FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --shell /bin/bash api_user

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements depuis le même dossier
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_pandemies.py .
COPY auth.py .
COPY db_config.py .

RUN chown -R api_user:api_user /app
USER api_user

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "api_pandemies:app", "--host", "0.0.0.0", "--port", "8000"]