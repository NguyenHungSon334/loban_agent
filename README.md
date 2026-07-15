# Agent Lỗ Ban — Hồn Đá

Trợ lý đọc bản vẽ khu lăng mộ → bóc tách kích thước → đối chiếu thước Lỗ Ban → đề xuất kích thước tốt → xuất **data JSON + PNG 4:5 + PDF A4**.

Chi tiết thiết kế & quyết định: [`plan.md`](plan.md).

## Cài đặt

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"              # thuần Python — không cần poppler/chromium/native
cp .env.example .env                 # điền LOBAN_GEMINI_API_KEY
```

## Chạy

```bash
loban run ban_ve.png --ho-so HS01 --khach-hang "Ông A" --dia-diem "Thanh Hóa" \
  --huong-cong "Ra ngoài" --vat-lieu "Đá xanh đen"
```

Đầu ra tại `output/HS01/`: `analysis.json`, `png_1.png…`, `report.pdf`.

Cờ: `--note "..."` (thông số nhân viên nhập), `--light` (Gemini flash rẻ hơn), `--no-png` / `--no-pdf`.

## Luồng xử lý

`ingest → extract (Gemini vision) → classify → suggest → validate → render`

- **Gemini** chỉ đọc số/nhãn trên bản vẽ (không tính cung — tránh ảo số).
- **Code deterministic** lo toàn bộ toán Lỗ Ban: tra cung, đề xuất, biên độ.

## Thước Lỗ Ban (data/loban_data.json)

| Thước | Dùng cho | Chu kỳ |
|-------|----------|--------|
| 52,2 cm (thông thủy) | cửa, cổng, lối đi | 522 mm / 8 cung |
| 42,9 cm (dương trạch) | cột, hàng rào, khối lăng | 429 mm / 8 cung |
| 38,8 cm (âm phần) | bàn thờ, hộp thờ, mộ | 388 mm / 10 cung |

Công thức: `cung = floor((L mod chu_kỳ) / bước_cung)`. Cờ `near_border` cảnh báo khi số cách biên cung xấu ≤ 10 mm (sai số thi công).

## Test

```bash
python -m pytest -q      # 43 test — toán cung, mapping, đề xuất, pipeline, HTML build
```

Test không cần key/browser (Gemini & render thật kiểm bằng tay khi có `.env` + Chromium).

## Cấu trúc

```
data/loban_data.json      # 3 thước
src/loban/
  ruler.py    classify.py   suggest.py    # toán Lỗ Ban (deterministic)
  extract.py  ingest.py     prompts/      # vision (Gemini)
  pipeline.py validate.py   models.py     # ghép chuỗi + schema
  render/     cli.py                       # đầu ra + CLI
tests/                                     # golden + unit
```

## Web UI (React + FastAPI)

Giao diện web bọc pipeline: tải bản vẽ → theo dõi tiến trình → xem báo cáo → tải JSON/PNG/PDF. Style theo `DESIGN.md`. Không auth (nội bộ LAN/VPS).

### Dev

```bash
# 1. Backend API (cần .env có LOBAN_GEMINI_API_KEY)
loban-web                            # uvicorn :8000 (asyncio job pool + SQLite web.db)

# 2. Frontend (terminal khác)
cd frontend && npm install && npm run dev   # Vite :5173, proxy /api → :8000
```

Mở http://localhost:5173.

### Prod (1 VPS)

```bash
cd frontend && npm run build         # tạo frontend/dist/
loban-web                            # FastAPI tự serve dist/ + API tại :8000
```

Chạy `loban-web` **1 process** (`--workers 1`) — asyncio pool sống trong process đó. Số job nặng song song chỉnh qua env `LOBAN_WEB_WORKER_CONCURRENCY` (mặc định 3, khớp RAM VPS). Nhiều máy → mới cần Redis/arq (chưa dùng).

### Kiến trúc web

```
src/loban/web/           app.py (6 API) · worker.py (asyncio pool) · db.py (SQLite) · jobs.py · deps.py
frontend/src/            pages/ (5 trang) · components/ · hooks/ · api/client.js · styles/tokens.css
```

Trang: `/` tạo phân tích · `/analyze/:hoSo` tiến trình · `/report/:hoSo` báo cáo · `/ho-so` lịch sử · `/thuoc` tra thước.

Test web: `pytest tests/test_web_api.py tests/test_worker.py tests/test_db.py` · `cd frontend && npm test`.

## Trạng thái

MVP hoàn chỉnh P1–P7. Cần cấp để hoàn thiện: `LOBAN_GEMINI_API_KEY`, tài sản thương hiệu (logo/màu/font — hiện placeholder), ảnh hồ sơ thật làm fixture verify extract.
