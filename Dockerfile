# syntax=docker/dockerfile:1.6

ARG NODE_VERSION=20
ARG PYTHON_VERSION=3.11

FROM node:${NODE_VERSION}-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend .
RUN npm run build

FROM python:${PYTHON_VERSION}-slim AS backend
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PATH="/app/backend/.venv/bin:${PATH}"
WORKDIR /app/backend
COPY backend .
RUN python -m venv .venv \
    && .venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:${PYTHON_VERSION}-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PATH="/app/backend/.venv/bin:${PATH}" \
    PORT=8000 \
    HOST=0.0.0.0 \
    FRONTEND_DIST=/app/frontend/dist
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends vim less curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=frontend /app/frontend/dist frontend/dist
COPY --from=backend /app/backend backend
COPY start.sh README.md .
EXPOSE 8000
CMD ["bash", "-c", "cd backend && .venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
