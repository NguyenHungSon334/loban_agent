import json

from loban.models import Dimension, ExtractionResult, Profile
from loban.pipeline import build_report
from loban.render.analysis_json import write_analysis
from loban.validate import MANDATORY_WARNING


def _extraction():
    return ExtractionResult(dimensions=[
        # tốt, tin cậy cao
        Dimension(label="Rộng mộ", category="mo", kind="phu_bi", value_mm=870, confidence="cao"),
        # xấu, cao -> có đề xuất, usable (lối đi 52.2 thông thủy, 160 -> xấu)
        Dimension(label="Lối đi", category="loi_di", kind="thong_thuy", value_mm=160, confidence="cao"),
        # tin cậy thấp -> need_confirm + không usable
        Dimension(label="Cổng mờ", category="cong", kind="thong_thuy", value_mm=2060, confidence="thap", need_confirm=True),
        # thiếu số -> need_confirm + không usable + khong_ap_dung
        Dimension(label="Cao lăng", category="lang_tho", kind="tong_the", value_mm=None, confidence="chua_xac_dinh"),
    ])


def test_report_structure():
    r = build_report(_extraction(), Profile(ho_so="HS01", khach_hang="A"))
    assert len(r.items) == 4
    assert r.warnings == [MANDATORY_WARNING]
    assert r.data_version

    by_label = {it.dimension.label: it for it in r.items}
    assert by_label["Rộng mộ"].loban.status == "tot"
    assert by_label["Rộng mộ"].usable is True
    assert by_label["Lối đi"].loban.status == "chua_phu_hop"
    assert by_label["Lối đi"].suggestion is not None
    assert by_label["Cổng mờ"].usable is False       # tin cậy thấp
    assert by_label["Cao lăng"].usable is False       # thiếu số
    assert by_label["Cao lăng"].loban.status == "khong_ap_dung"


def test_need_confirm_list():
    r = build_report(_extraction(), Profile(ho_so="HS01"))
    assert "Cổng mờ" in r.need_confirm
    assert "Cao lăng" in r.need_confirm
    assert "Rộng mộ" not in r.need_confirm


def test_write_analysis_roundtrip(tmp_path):
    r = build_report(_extraction(), Profile(ho_so="HS01"))
    f = write_analysis(r, tmp_path / "HS01")
    assert f.exists()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["profile"]["ho_so"] == "HS01"
    assert len(data["items"]) == 4
    # Unicode tiếng Việt giữ nguyên, không escape
    assert "Rộng mộ" in f.read_text(encoding="utf-8")
