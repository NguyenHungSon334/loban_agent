"""Chat: tra_cung deterministic + endpoint (mock Gemini)."""
from loban.chat import tra_cung


def test_tra_cung_mo():
    r = tra_cung(870, "38.8")          # mộ rộng 87cm
    assert r["cung"] == "Vượng" and r["tot"] is True
    assert r["cung_nho"] == "Hỷ sự"


def test_tra_cung_thong_thuy():
    r = tra_cung(2060, "52.2")         # lọt lòng cổng
    assert r["cung"] == "Tể Tướng" and r["tot"] is True


def test_tra_cung_ruler_sai():
    assert "loi" in tra_cung(500, "99.9")


def test_match_label():
    from loban.web.app import _match_label
    labels = ["Chiều rộng mộ", "Chiều dài mộ", "Lọt lòng cổng"]
    assert _match_label("Lọt lòng cổng", labels) == 2   # khớp đúng
    assert _match_label("cổng", labels) == 2             # substring, 1 khớp
    assert _match_label("mộ", labels) is None            # nhập nhằng 2 khớp
    assert _match_label("sân", labels) is None           # không khớp


def test_parse_mm():
    from loban.web.app import _parse_mm
    assert _parse_mm("đổi chiều rộng thành 490") == 490      # số trần >=100 -> mm
    assert _parse_mm("rộng 87cm") == 870                     # cm -> mm
    assert _parse_mm("cổng 1m2") == 1200                     # 1m2 -> 1200
    assert _parse_mm("dài 1m27") == 1270                     # 1m27 -> 1270
    assert _parse_mm("1.27m") == 1270
    assert _parse_mm("490mm") == 490
    assert _parse_mm("không có số") is None


def test_match_edit_label():
    from loban.web.app import _match_edit_label
    labels = ["Chiều rộng phủ bì mộ", "Chiều dài phủ bì mộ", "Lỗ thông thiên"]
    assert _match_edit_label("đổi chiều rộng thành 490", labels) == 0
    assert _match_edit_label("sửa chiều dài 1m27", labels) == 1
    assert _match_edit_label("đổi số nào đó", labels) is None   # không khớp


def test_chat_endpoint_mocked(monkeypatch):
    # không gọi Gemini thật — mock hàm chat
    import loban.chat as chatmod
    monkeypatch.setattr(chatmod, "chat", lambda *a, **k: "Mộ 87cm thuộc cung Vượng (tốt).")
    from fastapi.testclient import TestClient
    from loban.web import app as appmod
    c = TestClient(appmod.app)   # không 'with' -> không chạy lifespan/worker
    r = c.post("/api/chat", data={"message": "mộ 87 cung nào"})
    assert r.status_code == 200
    assert "Vượng" in r.json()["reply"]
