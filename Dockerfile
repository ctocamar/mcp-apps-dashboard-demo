# Imagen de la demo del servidor MCP `panel_metricas`.
# Usa uv para instalar dependencias de forma reproducible (a partir de uv.lock).
FROM python:3.12-slim

# Binario de uv (copiado desde la imagen oficial, sin instalar curl/pip extra).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# 1) Instalar dependencias primero (mejor caché de capas).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 2) Copiar el código de la app.
COPY server.py generate_preview.py ./
COPY metrics_app ./metrics_app

# 3) Instalar el propio proyecto en el entorno.
RUN uv sync --frozen --no-dev

# Transporte HTTP para poder "levantarlo fácil" con compose.
ENV MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "python", "server.py"]
