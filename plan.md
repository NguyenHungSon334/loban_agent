# PLAN — Agent Lỗ Ban (MVP)

> Trợ lý cho nhân viên kinh doanh Hồn Đá: đọc bản vẽ/ảnh → bóc tách kích thước → đối chiếu thước Lỗ Ban → đề xuất kích thước tốt → đóng gói data nội bộ + PNG 4:5 + PDF A4.
>
> Nguồn yêu cầu: `agent lỗ ban.docx`. Tài liệu này là bản kế hoạch triển khai để review trước khi code.

---

## 0. Quyết định đã chốt

| # | Vấn đề | Quyết định |
|---|--------|-----------|
| D1 | Nguồn dữ liệu Lỗ Ban | Dùng công thức chuẩn do Hồn Đá cấp (mục 5.1) — 3 thước, cung + tốt/xấu cố định. Không phụ thuộc runtime Wonder.vn |
| D9 | Xung đột tên cung ảnh mẫu | **CHỐT**: bỏ tên cung ảnh mẫu, dùng công thức mục 5.1 làm authoritative. Ảnh mẫu chỉ tham khảo layout, không dùng số cung. Golden test khoá theo công thức |
| D2 | Thước cho lăng thờ | **Tách**: khối kiến trúc → 42,9 (dương trạch); hộp thờ/bài vị → 38,8 (âm phần); thông thủy giữa cột → 52,2 |
| D2c | **3 thước theo loại** (2026-07-15, thay D2/D2b) | **Lối đi + bậc tam cấp → 42,9** (ưu tiên trước, kể cả đo thông thủy) · **khe thông thủy giữa 2 cột cổng (kind=thông thủy) → 52,2** · **còn lại (rào, cổng, mộ, lăng, cuốn thư, mặt bằng…) → 38,8**. Chỉ "không áp dụng" khi THIẾU số. |
| D10 | **Rule category→thước cấu hình được** (2026-07-15) | `data/category_rules.json` (`default_ruler`/`thong_thuy_ruler`/`category_ruler`), sửa qua UI trang Thước (`GET/PUT /api/rules`), `classify.ruler_for` đọc live. Override env test `LOBAN_RULES_PATH` |
| D11 | **Cung nhỏ** (data v2.0.0) | Mỗi cung lớn chia cung nhỏ (52,2→5 · 42,9→4 · 38,8→4), tên trong `loban_data.json`, kế thừa tốt/xấu từ cung lớn. `lookup` trả `sub_index/sub_name`, `LobanResult.cung_nho`, hiển thị "cung lớn › cung nhỏ" trên báo cáo + UI + thước trực quan |
| D3 | Format đầu ra | 3 loại: (1) data phân tích nội bộ JSON, (2) PNG 4:5, (3) PDF A4 ngang lưu hồ sơ |
| D4 | Xếp hạng cung | Mọi cung tốt ngang nhau — chọn cung tốt gần nhất, không rank ý nghĩa |
| D5 | Tài sản thương hiệu | MVP chưa cần đẹp — layout đơn giản, placeholder logo/màu, style hoá sau |
| D6 | Kích thước đã Tốt | Luôn hiện đề xuất dưới/trên (theo doc mục 7), kể cả khi đã đạt cung tốt |
| D7 | Số sát biên cung | Cảnh báo "rủi ro lệch cung khi thi công" nếu số cách biên cung xấu ≤ 10 mm |
| D8 | Biên độ điều chỉnh (QT5) | Giữ default doc: mộ ±50→±100, cổng ±50, lăng ±100, lối đi ưu tiên tăng |

Ưu tiên xử lý xung đột (doc mục 5, bất biến):
**An toàn/kết cấu → Công năng → Lỗ Ban → Tỷ lệ kiến trúc → Thẩm mỹ.**

---

## 1. Phạm vi MVP

### Trong phạm vi
- Đọc: ảnh bản vẽ kỹ thuật, bản vẽ tay, mặt bằng có ghi chú, PDF, văn bản thông số.
- Bóc tách kích thước **nhìn thấy rõ** (không suy đoán khi thiếu tỷ lệ).
- Phân loại theo 3 thước Lỗ Ban, tra cung, chấm tốt/chưa phù hợp.
- Đề xuất kích thước tốt gần nhất (dưới + trên) trong biên độ cho phép.
- Gán độ tin cậy từng kích thước; đánh dấu "Cần xác nhận".
- Xuất 3 định dạng đầu ra.

### Ngoài phạm vi (MVP)
- Tự suy kích thước khi bản vẽ không có tỷ lệ/mốc chuẩn.
- Phân tích từng thớt đá.
- Chiều cao tổng (mộ/lăng) — chỉ khi khách yêu cầu.
- Tự sửa bản vẽ hoặc quyết định kích thước sản xuất cuối cùng.
- Xếp hạng ý nghĩa cung.

### Hạng mục bóc tách (doc mục 3)
| Nhóm | Kích thước | Thước áp dụng |
|------|-----------|---------------|
| A. Mặt bằng khu | dài/rộng khu đất, kích thước tổng thể | tham chiếu, không bắt buộc Lỗ Ban |
| B. Mộ | rộng phủ bì, dài phủ bì, (cao tổng nếu có), lọt lòng tiểu/quan tài | phủ bì → **38,8**; lọt lòng → phân tích riêng |
| C. Cổng | rộng thông thủy, cao thông thủy, lọt lòng giữa 2 trụ | **52,2** (không lấy phủ bì thay thông thủy) |
| D. Lối đi & khoảng cách | rộng lối đi (2 biên rõ), khoảng cách mộ–mộ / mộ–tường / mộ–lăng | lối đi → **52,2**; khoảng cách kỹ thuật → công năng ưu tiên |
| E. Lăng thờ | dài/rộng tổng khối, hộp thờ, thông thủy cột, bệ/thân | khối → **42,9**; hộp thờ → **38,8**; thông thủy → **52,2** |

---

## 2. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT (ảnh / PDF / text) + metadata hồ sơ (nhân viên nhập)  │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │  1. INGEST                            │
        │  - chuẩn hoá input (ảnh/PDF→ảnh, text) │
        │  - đọc metadata hồ sơ                  │
        └───────────────────┬───────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │  2. EXTRACT (Vision — Gemini multimodal) │
        │  - bóc tách kích thước nhìn thấy       │
        │  - gán: loại kích thước, vị trí, đơn vị │
        │  - gán độ tin cậy + cờ "Cần xác nhận"  │
        │  → EXTRACTION SCHEMA (JSON)            │
        └───────────────────┬───────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │  3. CLASSIFY (deterministic, code)     │
        │  - map hạng mục → thước (bảng D2)      │
        │  - tra cung từ loban_data.json         │
        │  - chấm tốt/chưa phù hợp               │
        │  - cảnh báo sát biên (±10mm)           │
        └───────────────────┬───────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │  4. SUGGEST (deterministic, code)      │
        │  - tìm cung tốt gần nhất dưới/trên     │
        │  - áp biên độ QT5                      │
        │  - tính chênh lệch, ghi khuyến nghị    │
        └───────────────────┬───────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │  5. VALIDATE                          │
        │  - loại kích thước tin cậy Thấp khỏi   │
        │    kết luận cuối                       │
        │  - gom danh sách "Cần xác nhận"        │
        └───────────────────┬───────────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │  6. RENDER                            │
        │  - (1) analysis.json  (data nội bộ)   │
        │  - (2) PNG 4:5                        │
        │  - (3) PDF A4 ngang  (hồ sơ)          │
        └───────────────────────────────────────┘
```

**Nguyên tắc chia trách nhiệm:**
- **Vision (LLM)** chỉ làm việc mắt: đọc số, đọc nhãn, định vị. Không tính cung, không đề xuất.
- **Code deterministic** làm toàn bộ toán Lỗ Ban (tra cung, đề xuất, biên độ). Lý do: kết quả phải lặp lại được, kiểm thử được, không "ảo số".

---

## 3. Techstack

| Lớp | Lựa chọn | Lý do |
|-----|----------|-------|
| Ngôn ngữ | **Python 3.12** | hệ sinh thái ảnh/PDF mạnh, dễ test |
| Vision/LLM | **Gemini API** (`gemini-2.5-pro` bóc tách chính, `gemini-2.5-flash` cho ảnh đơn giản/rẻ) qua SDK **google-genai** | đọc bản vẽ + trả JSON; ép schema bằng `response_mime_type="application/json"` + `response_schema` (nhận pydantic model) |
| Đọc PDF | **PyMuPDF** (fitz) render trang→ảnh | wheel thuần, KHÔNG cần poppler → deploy hosting dễ (bỏ pdf2image/pypdf) |
| Xử lý ảnh | **Pillow** | crop/resize/vẽ overlay |
| Toán Lỗ Ban | thuần Python (module `loban/`) | deterministic, không phụ thuộc |
| Data Lỗ Ban | **JSON** (`loban_data.json`) | dễ đọc, dễ sửa, versioned |
| Validate schema | **pydantic v2** | ép kiểu extraction/analysis, fail fast tại boundary |
| PDF (A4 + 4:5) | **fpdf2** (thuần Python, font DejaVu bundle) | không browser/native → deploy hosting share được |
| PNG 4:5 | **fpdf2** dựng PDF 4:5 → **PyMuPDF** render PNG 1080×1350 | tái dùng fitz; bỏ Playwright/Chromium |
| Test | **pytest** | golden cases cho toán cung |
| Config | `.env` + pydantic-settings | API key, đường dẫn asset |
| CLI/entry | **Typer** (hoặc argparse) | chạy `loban run <input> --profile ...` |

> Ponytail note: HTML template dùng chung cho cả PNG và PDF — một layout engine, hai output. Không viết 2 bộ render. Nếu sau này PNG cần layout khác hẳn PDF thì tách.

**Bỏ qua ở MVP** (thêm khi cần): OCR riêng (Tesseract) — để Gemini vision lo; DB — mỗi hồ sơ là 1 thư mục file; web UI — chạy CLI trước.

---

## 4. Cấu trúc project

```
agent_lo_ban/
├── plan.md                       # tài liệu này
├── agent lỗ ban.docx             # spec gốc
├── pyproject.toml
├── .env.example
├── data/
│   └── loban_data.json           # 3 thước, cung, khoảng mm  (nền tảng)
├── src/loban/
│   ├── __init__.py
│   ├── config.py                 # settings, đường dẫn, API key
│   ├── models.py                 # pydantic: Dimension, Analysis, Suggestion...
│   ├── ingest.py                 # input → ảnh/text chuẩn hoá
│   ├── extract.py                # gọi Gemini vision → ExtractionResult
│   ├── ruler.py                  # nạp loban_data, tra cung từ mm
│   ├── classify.py               # map hạng mục→thước, chấm tốt/xấu, cảnh báo biên
│   ├── suggest.py                # đề xuất dưới/trên + biên độ QT5
│   ├── validate.py               # lọc độ tin cậy, gom "cần xác nhận"
│   ├── render/
│   │   ├── analysis_json.py      # đầu ra 1
│   │   ├── png.py                # đầu ra 2 (4:5)
│   │   ├── pdf_report.py         # đầu ra 3 (A4 ngang)
│   │   └── templates/            # HTML/Jinja2 dùng chung
│   ├── prompts/
│   │   └── extract_system.md     # system prompt cho bước vision
│   └── cli.py                    # entry point
├── tests/
│   ├── test_ruler.py             # golden cases tra cung
│   ├── test_classify.py
│   ├── test_suggest.py           # biên độ, cận biên
│   └── fixtures/                 # ảnh mẫu + kết quả kỳ vọng
└── output/                       # hồ sơ xuất ra (gitignore)
    └── <ho_so>/
        ├── analysis.json
        ├── png_1.png
        └── report.pdf
```

---

## 5. Mô hình dữ liệu

### 5.1 `loban_data.json` (nền tảng — số chính thức)

Công thức chung: `vị_trí = (L mod chu_kỳ) / bước_cung`, lấy `floor(vị_trí)` = chỉ số cung (0-based). Biên cung: `[i*bước, (i+1)*bước)`.

**Thước Thông Thủy 52,2 cm** — khoảng thông thủy (cửa, cửa sổ, cổng, lối đi). Chu kỳ 522 mm, 8 cung × 65,25 mm:

| # | Cung | Tốt/Xấu | start_mm | end_mm |
|---|------|---------|----------|--------|
| 1 | Quý Nhân | Tốt | 0 | 65,25 |
| 2 | Hiểm Họa | Xấu | 65,25 | 130,5 |
| 3 | Thiên Tai | Xấu | 130,5 | 195,75 |
| 4 | Thiên Tài | Tốt | 195,75 | 261 |
| 5 | Phúc Lộc | Tốt | 261 | 326,25 |
| 6 | Cô Độc | Xấu | 326,25 | 391,5 |
| 7 | Thiên Tặc | Xấu | 391,5 | 456,75 |
| 8 | Tể Tướng | Tốt | 456,75 | 522 |

**Thước Dương Trạch 42,9 cm** — khối xây dựng (bếp, bệ, bậc, cột, hàng rào, khối lăng). Chu kỳ 429 mm, 8 cung × 53,625 mm:

| # | Cung | Tốt/Xấu | start_mm | end_mm |
|---|------|---------|----------|--------|
| 1 | Tài | Tốt | 0 | 53,625 |
| 2 | Bệnh | Xấu | 53,625 | 107,25 |
| 3 | Ly | Xấu | 107,25 | 160,875 |
| 4 | Nghĩa | Tốt | 160,875 | 214,5 |
| 5 | Quan | Tốt | 214,5 | 268,125 |
| 6 | Kiếp | Xấu | 268,125 | 321,75 |
| 7 | Hại | Xấu | 321,75 | 375,375 |
| 8 | Bản | Tốt | 375,375 | 429 |

**Thước Âm Phần 38,8 cm** — đồ nội thất/âm phần (bàn thờ, tủ, hộp thờ, mộ). Chu kỳ 388 mm, 10 cung × 38,8 mm:

| # | Cung | Tốt/Xấu | start_mm | end_mm |
|---|------|---------|----------|--------|
| 1 | Đinh | Tốt | 0 | 38,8 |
| 2 | Hại | Xấu | 38,8 | 77,6 |
| 3 | Vượng | Tốt | 77,6 | 116,4 |
| 4 | Khổ | Xấu | 116,4 | 155,2 |
| 5 | Nghĩa | Tốt | 155,2 | 194 |
| 6 | Quan | Tốt | 194 | 232,8 |
| 7 | Tử | Xấu | 232,8 | 271,6 |
| 8 | Thất | Xấu | 271,6 | 310,4 |
| 9 | Hưng | Tốt | 310,4 | 349,2 |
| 10 | Tài | Tốt | 349,2 | 388 |

JSON (rút gọn 1 thước, 2 thước còn lại cùng cấu trúc):
```jsonc
{
  "version": "1.0.0",
  "updated": "2026-07-14",
  "source": "công thức chuẩn Hồn Đá cấp; đối chiếu Wonder.vn",
  "rulers": {
    "52.2": {
      "usage": "thông thủy: cửa, cửa sổ, cổng, lối đi",
      "cycle_mm": 522, "step_mm": 65.25,
      "cung": [
        { "name": "Quý Nhân", "good": true,  "start_mm": 0,      "end_mm": 65.25 },
        { "name": "Hiểm Họa", "good": false, "start_mm": 65.25,  "end_mm": 130.5 },
        { "name": "Thiên Tai","good": false, "start_mm": 130.5,  "end_mm": 195.75 },
        { "name": "Thiên Tài","good": true,  "start_mm": 195.75, "end_mm": 261 },
        { "name": "Phúc Lộc", "good": true,  "start_mm": 261,    "end_mm": 326.25 },
        { "name": "Cô Độc",   "good": false, "start_mm": 326.25, "end_mm": 391.5 },
        { "name": "Thiên Tặc","good": false, "start_mm": 391.5,  "end_mm": 456.75 },
        { "name": "Tể Tướng", "good": true,  "start_mm": 456.75, "end_mm": 522 }
      ]
    },
    "42.9": { "usage": "khối xây dựng: bếp, bệ, bậc, cột, hàng rào, khối lăng", "cycle_mm": 429, "step_mm": 53.625, "cung": [ /* Tài,Bệnh,Ly,Nghĩa,Quan,Kiếp,Hại,Bản */ ] },
    "38.8": { "usage": "âm phần/nội thất: bàn thờ, tủ, hộp thờ, mộ", "cycle_mm": 388, "step_mm": 38.8, "cung": [ /* Đinh,Hại,Vượng,Khổ,Nghĩa,Quan,Tử,Thất,Hưng,Tài */ ] }
  }
}
```

### 5.2 Pydantic models (rút gọn)
```python
class Dimension(BaseModel):
    label: str                 # "Chiều rộng mộ", "Lọt lòng cổng"...
    category: Literal["mo","cong","loi_di","khoang_cach","lang_tho","mat_bang"]
    kind: Literal["phu_bi","thong_thuy","lot_long","khoi","tong_the"]
    value_mm: float | None
    location: str              # vị trí trên bản vẽ
    confidence: Literal["cao","trung_binh","thap","chua_xac_dinh"]
    need_confirm: bool
    estimated: bool            # True nếu suy theo tỷ lệ

class LobanResult(BaseModel):
    ruler: Literal["38.8","42.9","52.2"] | None
    cung: str | None
    cung_good: bool | None
    near_border: bool          # sát biên ≤10mm
    status: Literal["tot","chua_phu_hop","khong_ap_dung"]

class Suggestion(BaseModel):
    lower_mm: float | None
    lower_cung: str | None
    upper_mm: float | None
    upper_cung: str | None
    delta_lower: float | None
    delta_upper: float | None
    note: str                  # khuyến nghị theo ưu tiên kỹ thuật

class AnalyzedItem(BaseModel):
    dimension: Dimension
    loban: LobanResult
    suggestion: Suggestion | None

class Profile(BaseModel):       # metadata hồ sơ
    ho_so: str
    khach_hang: str | None
    dia_diem: str | None
    huong_cong: str | None
    vat_lieu: str | None
    dien_tich_m2: float | None
```

---

## 6. Thuật toán lõi

### 6.1 Tra cung (`ruler.py`)
```
pos = value_mm % cycle_mm
tìm cung có start_mm <= pos < end_mm
→ trả (cung, good)
near_border = khoảng cách từ pos tới biên cung XẤU gần nhất <= 10mm
```

### 6.2 Đề xuất (`suggest.py`)
```
Nếu status == "tot" và không near_border → vẫn liệt kê dưới/trên (D6) nhưng note "đang đạt".
Tìm trong biên độ theo hạng mục (D8):
  - quét xuống: value tốt gần nhất < hiện tại
  - quét lên:   value tốt gần nhất > hiện tại
  - lối đi: chỉ đề xuất giảm nếu vẫn đủ công năng; ưu tiên tăng
Nếu không có trong biên độ → note "Cần kiến trúc sư điều chỉnh mặt bằng".
delta = |đề xuất - hiện tại|
```

### 6.3 Ưu tiên xung đột
Trước khi đề xuất giữ/sửa: nếu vi phạm công năng (vd lối đi quá hẹp) → không đề xuất giữ dù đạt cung. Ghi rõ lý do kỹ thuật.

---

## 7. System prompt (bước Extract)

`prompts/extract_system.md` — điểm chính:
- Vai trò: đọc bản vẽ/ảnh, **chỉ bóc tách kích thước nhìn thấy rõ**.
- Cấm: điền số mờ, đoán theo hình dáng, mượn số sản phẩm tương tự, suy tỷ lệ khi không có mốc.
- Ưu tiên nguồn số: ghi trực tiếp bản vẽ → khách xác nhận → nhân viên nhập → suy tỷ lệ (chỉ khi có tỷ lệ/mốc).
- Mỗi kích thước phải gán: loại (phủ bì/thông thủy/lọt lòng/khối), vị trí, độ tin cậy, cờ cần xác nhận.
- Output: **JSON đúng schema** (ép bằng `response_schema` của Gemini), không văn xuôi.
- Glossary bắt buộc trong prompt: phủ bì = mép ngoài; thông thủy = khoảng trống lọt sáng/lọt lòng giữa 2 mép; lọt lòng = kích thước trong lòng cấu kiện.

Toán cung **không** nằm trong prompt — code lo.

---

## 8. Kiểm thử

- `test_ruler.py`: golden cases — mm → cung kỳ vọng **tính theo công thức mục 5.1** (không theo ảnh mẫu):

| Thước | L (mm) | L mod cycle | vị trí | Cung | Tốt/Xấu |
|-------|--------|-------------|--------|------|---------|
| 38.8 | 870 | 94 | 2.42 | Vượng | Tốt |
| 38.8 | 1270 | 106 | 2.73 | Vượng | Tốt |
| 38.8 | 2500 | 172 | 4.43 | Nghĩa | Tốt |
| 38.8 | 790 | 14 | 0.36 | Đinh | Tốt |
| 38.8 | 2830 | 114 | 2.94 | Vượng | Tốt |
| 52.2 | 610 | 88 | 1.35 | Hiểm Họa | Xấu |
| 52.2 | 2060 | 494 | 7.57 | Tể Tướng | Tốt |
| 52.2 | 522 | 0 | 0.00 | Quý Nhân | Tốt |
| 42.9 | 250 | 250 | 4.66 | Quan | Tốt |
| 42.9 | 590 | 161 | 3.00 | Nghĩa | Tốt (sát biên — cách biên Ly 0,125 mm → near_border) |
| 42.9 | 1880 | 164 | 3.06 | Nghĩa | Tốt |

⚠️ Vài số này khác tên cung ảnh mẫu (D9) — chủ đích, công thức là chuẩn.
- `test_classify.py`: map hạng mục→thước đúng (D2); cờ near_border kích khi ≤10mm.
- `test_suggest.py`: biên độ QT5; case không có phương án → "Cần KTS".
- Ít nhất 1 fixture ảnh chạy end-to-end (Phase 4).

> Ponytail: chỉ assert-based test cho toán cung + đề xuất (đường tiền/an toàn nghiệp vụ). Không test render pixel.

---

## 9. Cảnh báo bắt buộc (in trên PNG + PDF)
> "Kết quả đối chiếu Lỗ Ban xây dựng trên thông số hiện có. Các kích thước 'Cần xác nhận' phải kiểm tra lại trên bản vẽ kỹ thuật hoặc tại hiện trường trước khi sản xuất/thi công. Sai số thi công ±10 mm."

Kích thước tin cậy **Thấp** không dùng để kết luận cuối.

---

## 10. Lộ trình (phases)

| Phase | Nội dung | Đầu ra kiểm được |
|-------|----------|------------------|
| **P1** | `loban_data.json` + `ruler.py` + golden test | `pytest test_ruler.py` xanh, khớp ảnh mẫu |
| **P2** | models + `classify.py` + `suggest.py` + test | logic Lỗ Ban chạy trên input giả lập |
| **P3** | `extract.py` (Gemini vision) + system prompt + schema ép | ảnh thật → extraction JSON đúng |
| **P4** | `render/analysis_json.py` → đầu ra 1 | analysis.json hoàn chỉnh 1 hồ sơ |
| **P5** | template HTML + `png.py` (4:5) | PNG ≤5–7 kích thước/ảnh, tự chia trang |
| **P6** | `pdf_report.py` (A4 ngang) | PDF hồ sơ nhiều trang |
| **P7** | `cli.py` gắn chuỗi + `.env` + README | `loban run <input>` chạy full |

Mỗi phase review được độc lập. P1 là gốc — sai data thì mọi thứ sai.

---

## 11. Việc cần Hồn Đá cấp (không chặn P1–P2)
- Logo, watermark "thổi hồn vào đá", bảng màu, font (P5 — hiện dùng placeholder).
- Xác nhận danh sách cung + khoảng mm nếu công ty có chuẩn riêng khác dân gian.
- Ví dụ hồ sơ thật (ảnh + kết quả mong muốn) làm fixture P3–P4.

---

## 12. Rủi ro & giảm thiểu
| Rủi ro | Giảm thiểu |
|--------|-----------|
| Vision đọc sai/thiếu số trên bản vẽ mờ | ép cờ độ tin cậy + "cần xác nhận"; không kết luận trên tin cậy Thấp |
| Dataset cung sai lệch | golden test khoá bằng số tính theo công thức mục 5.1 (D9) |
| Nhầm loại kích thước (phủ bì vs thông thủy) → sai thước | glossary trong prompt + trường `kind` bắt buộc |
| Số sát biên cung, sai số thi công lệch cung | cờ near_border cảnh báo (D7) |
| Wonder đổi giao diện | không phụ thuộc runtime; data nội bộ versioned |

---

## Trạng thái
Toàn bộ quyết định D1–D9 đã chốt. Techstack: Python + Gemini + Playwright.

**Đã xong P1–P7** (43 test xanh):
- P1 `loban_data.json` + `ruler.py` — tra cung + near_border
- P2 `models.py` + `classify.py` + `suggest.py` — mapping D2, đề xuất QT5
- P3 `config.py` + `extract.py` + `ingest.py` + system prompt — Gemini vision (chờ key verify)
- P4 `validate.py` + `pipeline.py` + `render/analysis_json.py` — đầu ra 1
- P5/P6 `render/` templates + `png.py` + `pdf_report.py` — PNG 4:5 + PDF A4 (Playwright)
- P7 `cli.py` + README

**Còn chờ cấp**: `LOBAN_GEMINI_API_KEY` (verify extract ảnh thật), tài sản thương hiệu (logo/màu/font), ảnh hồ sơ thật làm fixture.

---

# PHẦN 2 — WEB UI (P8+)

> Web bọc mỏng pipeline sẵn có: form → `build_report` → hiện `AnalysisReport` + tải 3 file. **Không** viết lại toán/render. Style theo `DESIGN.md` (Cal.com-like).

## W0. Quyết định đã chốt

| # | Vấn đề | Quyết định |
|---|--------|-----------|
| W-D1 | Frontend | **React 18 + Vite (JSX)** SPA |
| W-D2 | Backend web | **FastAPI** async, trả JSON, phục vụ `dist/` + 3 file output |
| W-D3 | Job nền | **asyncio worker pool + `Semaphore(N)`** trong 1 process — KHÔNG Redis/Celery. Lý do: 1 VPS, bước chậm là Gemini network-I/O; async đủ. Nâng arq+Redis chỉ khi nhiều máy |
| W-D4 | State job/hồ sơ | **SQLite + SQLModel** (bảng `Job`, `HoSo`) — sống qua restart; startup requeue job `running`→`queued` |
| W-D5 | Auth | **Không** — nội bộ LAN/VPS, mở |
| W-D6 | Deploy | 1 VPS, 1 process uvicorn (`--workers 1`); dev Vite `:5173` proxy `/api`→uvicorn `:8000`; prod `vite build`→FastAPI serve `dist/` |
| W-D7 | Font | Cal Sans licensed → **Inter 600 `-0.04em`** thay (DESIGN §Known Gaps). Manrope 700 nếu muốn sau |
| W-D8 | Concurrency an toàn | mỗi POST tạo `ho_so` unique (mã + timestamp nếu trùng) tránh 2 nhân viên đè output |

> Ponytail: async-pool+SQLite = đúng mức cho 1 VPS nội bộ. `worker.py` bọc interface `enqueue/get_status` → thay ruột bằng arq khi cần nhiều máy chỉ đụng 1 file.

## W1. Techstack

| Lớp | Chọn |
|-----|------|
| API | FastAPI (async) |
| Job | asyncio worker pool + `Semaphore` (cap qua `WORKER_CONCURRENCY`); render fpdf2/fitz thuần Python → `run_in_executor` |
| DB | SQLite + SQLModel; `create_all` (chưa cần Alembic) |
| Frontend | React 18 + Vite |
| Router / server-state / form | react-router-dom / TanStack Query / react-hook-form |
| HTTP | `fetch` bọc mỏng (không axios) |
| Style | CSS Modules + `tokens.css` (DESIGN.md) |
| Test | pytest (API + worker + db) · Vitest + RTL (frontend) |

Thêm dep `pyproject.toml`: `fastapi`, `uvicorn[standard]`, `python-multipart`, `sqlmodel`.
Frontend deps: `react-router-dom @tanstack/react-query react-hook-form`.

## W2. API endpoints

| Method | Path | Việc |
|--------|------|------|
| POST | `/api/analyze` | multipart: file bản vẽ + profile fields + flags (`light/png/pdf`) → tạo Job `queued`, trả `ho_so` |
| GET | `/api/jobs/{ho_so}` | status: `queued/extract/classify/render/done/error` + step + error |
| GET | `/api/report/{ho_so}` | `AnalysisReport` JSON (từ `analysis.json`) |
| GET | `/api/ho-so` | list từ DB (mã, khách, ngày, #dim, status) — phân trang |
| GET | `/api/rulers` | `loban_data.json` |
| GET | `/api/files/{ho_so}/{name}` | tải json/png/pdf |

Pydantic models core đã có → FastAPI serialize sẵn, không viết lại schema.

## W3. Trang (5 route)

1. `/` **Tạo phân tích** — hero-band + `feature-card` chứa form: upload drag-drop (ảnh/PDF), field hồ sơ = `text-input` (mã hồ sơ*, khách, địa điểm, hướng cổng, vật liệu, ghi chú), flags = `nav-pill-group`, `button-primary`. Submit → POST → nav `/analyze/:hoSo`.
2. `/analyze/:hoSo` **Đang xử lý** — TanStack Query poll `/api/jobs`, skeleton + bước hiện tại. `done`→nav `/report`; `error`→callout.
3. `/report/:hoSo` **Báo cáo** — preview bản vẽ (`hero-app-mockup-card`); bảng kích thước (`product-mockup-card`): label/value_mm/thước/cung/status; `CungBadge` Tốt=`success` / Chưa phù hợp=`error` / near_border=`badge-orange`; cột đề xuất lower/upper mm + delta; callout "Cần xác nhận" + `MANDATORY_WARNING` (`cta-band-light`); 3 `button-secondary` tải JSON/PNG/PDF.
4. `/ho-so` **Lịch sử** — grid `feature-card` (phân trang), click → (3).
5. `/thuoc` **Tra thước** — 3 bảng cung read-only từ `/api/rulers`, badge tốt/xấu.

Chung: `<TopNav>` (wordmark Hồn Đá + Phân tích/Hồ sơ/Thước) + `<Footer>` dark đóng trang.

## W4. Cấu trúc folder

```
src/loban/web/
  __init__.py
  app.py            # FastAPI: 6 endpoints + serve dist/ + startup requeue
  db.py             # SQLModel engine, Job/HoSo models, session
  worker.py         # asyncio pool: queued → extract→build_report→render; Semaphore
  jobs.py           # enqueue, update status, query
  deps.py           # loban_data, đường dẫn output, settings (WORKER_CONCURRENCY)
  schemas.py        # request/response (nếu khác models core)

frontend/
  index.html  vite.config.js  package.json
  src/
    main.jsx
    api/client.js
    styles/{tokens.css, global.css}
    components/{TopNav,Footer,Button,TextInput,Card,Badge,PillGroup,
                DimensionTable,CungBadge,Skeleton}.jsx
    pages/{NewAnalysis,Analyzing,Report,History,Rulers}.jsx
    hooks/{useJob,useReport}.js
  tests/{NewAnalysis,DimensionTable}.test.jsx

tests/
  test_web_api.py   # routes 200, analyze tạo job, validate ho_so
  test_worker.py    # extraction stub → done, concurrency cap
  test_db.py        # Job state transitions
```

## W5. Lộ trình (phases)

| Phase | Nội dung | Đầu ra kiểm được |
|-------|----------|------------------|
| **P8** | `db.py` + `jobs.py` + `worker.py` (async pool + semaphore, extraction stub) + `test_worker.py`/`test_db.py` | job stub chạy nền, cap concurrency, state đúng — GỐC |
| **P9** | `app.py` 6 endpoints + startup requeue + `test_web_api.py` | API xanh không cần frontend |
| **P10** | Vite scaffold + `tokens.css`/`global.css` + TopNav/Footer/Button/Card/Badge | primitives + shell chạy |
| **P11** | Trang 1 (form POST) + trang 5 (rulers) | tạo job từ UI + tra thước |
| **P12** | Trang 2 (poll) + trang 3 (DimensionTable + tải) | end-to-end 1 hồ sơ trên web |
| **P13** | Trang 4 lịch sử (phân trang) + Vitest + README web | full UI |

P8 gốc — sai concurrency/state thì mọi thứ sai.

## W6. Việc còn chờ cấp
- Tài sản thương hiệu (logo/wordmark Hồn Đá, watermark "thổi hồn vào đá", màu nếu khác DESIGN.md) — P10.
- Font Cal Sans (nếu công ty mua license) — mặc định Inter 600 thay.

## W7. Trạng thái web (đã xong P8–P13)

| Phase | Xong | Test |
|-------|------|------|
| P8 `db.py`+`jobs.py`+`worker.py` (async pool, cap concurrency) | ✅ | `test_db.py`(4) `test_worker.py`(2) |
| P9 `app.py` 6 endpoint + lifespan requeue | ✅ | `test_web_api.py`(6) |
| P10 Vite scaffold + tokens/global + TopNav/Footer/Button/Card/Badge | ✅ | build xanh |
| P11 NewAnalysis form + Rulers + TextInput | ✅ | `NewAnalysis.test.jsx`(2) |
| P12 Analyzing(poll) + Report + DimensionTable/CungBadge + hooks | ✅ | `DimensionTable.test.jsx`(4) |
| P13 History (phân trang) + README web | ✅ | `History.test.jsx`(1) |

Backend 55 pytest xanh (43 core + 12 web). Frontend 7 vitest xanh, `vite build` xanh.

**Còn chờ**: `LOBAN_GEMINI_API_KEY` verify extract ảnh thật end-to-end trên web; tài sản thương hiệu; (tùy) self-host font Inter thay Google Fonts CDN.
