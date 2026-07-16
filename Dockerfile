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

# ưu tiên wheel dựng sẵn -> khỏi biên dịch nguồn (chậm/OOM trên e2-micro)
ENV PIP_PREFER_BINARY=1 PIP_NO_CACHE_DIR=1

# Cài DEPS trước, chỉ phụ thuộc pyproject.toml -> lớp này được cache lại,
# đổi code trong src/ KHÔNG bắt cài lại deps (tránh 36 phút mỗi deploy).
COPY pyproject.toml ./
RUN python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); open('/tmp/reqs.txt','w').write('\n'.join(d['project']['dependencies']))" \
    && pip install -r /tmp/reqs.txt

# editable install (link package, không cài lại deps) -> nhanh, chạy mỗi khi đổi src.
# giữ package tại /app/src/loban để build.py/ruler.py tính đúng đường dẫn theo __file__.
COPY src/ ./src/
RUN pip install --no-deps -e .

COPY data/ ./data/
COPY assests/ ./assests/
COPY --from=frontend /fe/dist ./frontend/dist

# state ghi ra volume /data (SQLite + output hồ sơ) — bền qua restart/redeploy
ENV LOBAN_WEB_OUTPUT_DIR=/data/output \
    LOBAN_WEB_DB_URL=sqlite:////data/web.db
EXPOSE 8000

CMD ["uvicorn", "loban.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
