# ─ Stage 1: build frontend (Vite) ─
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # -> /fe/dist

# ─ Stage 2: runtime Python ─
FROM python:3.11-slim
WORKDIR /app

# editable install: giữ package tại /app/src/loban để build.py/ruler.py tính đúng
# đường dẫn assests/ data/ frontend/dist theo __file__ (parents[...]).
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

COPY data/ ./data/
COPY assests/ ./assests/
COPY --from=frontend /fe/dist ./frontend/dist

# state ghi ra volume /data (SQLite + output hồ sơ) — bền qua restart/redeploy
ENV LOBAN_WEB_OUTPUT_DIR=/data/output \
    LOBAN_WEB_DB_URL=sqlite:////data/web.db
EXPOSE 8000

CMD ["uvicorn", "loban.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
