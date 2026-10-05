FROM python:3.11-slim

WORKDIR /app

# Instalação de utilitários de sistema e bibliotecas para Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalação das dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cópia do código-fonte e assets
COPY . /app

EXPOSE 8001

ENV PYTHONUNBUFFERED=1
ENV PORT=8001

CMD ["python", "api_backend.py"]
