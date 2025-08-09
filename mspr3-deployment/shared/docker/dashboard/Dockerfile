

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --shell /bin/bash streamlit_user

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements depuis le même dossier
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY streamlit_auth.py .

RUN mkdir -p /app/.streamlit && \
    echo "[server]" > /app/.streamlit/config.toml && \
    echo "port = 8501" >> /app/.streamlit/config.toml && \
    echo "address = \"0.0.0.0\"" >> /app/.streamlit/config.toml && \
    echo "headless = true" >> /app/.streamlit/config.toml && \
    echo "enableCORS = false" >> /app/.streamlit/config.toml

RUN chown -R streamlit_user:streamlit_user /app
USER streamlit_user

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
