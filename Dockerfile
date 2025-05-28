# Stage 1: Builder stage
FROM python:3.10-slim as builder

WORKDIR /app

# Instalar dependências de compilação
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Instalar Poetry
ENV POETRY_VERSION=2.1.3
RUN pip install --user --no-cache-dir "poetry==$POETRY_VERSION"

# Configurar Poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="/root/.local/bin:${PATH}"

# Copiar apenas as dependências primeiro
COPY pyproject.toml poetry.lock ./

# Instalar dependências de produção
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Copiar o entrypoint
COPY entrypoint.sh /app/entrypoint.sh

# Copiar código fonte
COPY src ./src

# Stage 2: Runtime stage
FROM python:3.10-slim as runtime

WORKDIR /app

# Instalar dependências de runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Copiar artefatos do builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Configurar environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:${PATH}"

# Usuário não-root
RUN useradd -m -u 1001 appuser
USER appuser

# Porta da aplicação
EXPOSE 8000

# Comando de execução
CMD ["uvicorn", "lucid_docs.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--no-server-header"]