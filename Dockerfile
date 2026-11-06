# syntax=docker/dockerfile:1

# ---- Frontend build -------------------------------------------------------
FROM node:22-bookworm-slim AS web
WORKDIR /web
ENV npm_config_fund=false \
    npm_config_audit=false
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --include=optional
COPY frontend/ ./
RUN npm run build

# ---- Runtime --------------------------------------------------------------
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY frontend/public/ ./frontend/public/
COPY --from=web /web/dist/ ./frontend/dist/

# Persistent SQLite volume is mounted here (Azure Files).
RUN mkdir -p /app/data

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
