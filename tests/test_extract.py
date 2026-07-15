"""Test bước extract KHÔNG cần key/SDK: chỉ phần parse + ingest boundary.

Gọi Gemini thật để P3 sau (cần LOBAN_GEMINI_API_KEY).
"""
import json

import pytest

from loban.extract import _parse
from loban.ingest import load_inputs
from loban.models import Dimension, ExtractionResult


class _Resp:
    def __init__(self, parsed=None, text=None):
        self.parsed = parsed
        self.text = text


def test_parse_uses_parsed_when_pydantic():
    er = ExtractionResult(dimensions=[Dimension(label="x", category="mo", kind="phu_bi", value_mm=870)])
    assert _parse(_Resp(parsed=er)) is er


def test_parse_fallback_from_text():
    payload = {"dimensions": [{"label": "Rộng mộ", "category": "mo", "kind": "phu_bi", "value_mm": 870}]}
    out = _parse(_Resp(parsed=None, text=json.dumps(payload)))
    assert isinstance(out, ExtractionResult)
    assert out.dimensions[0].value_mm == 870


def test_parse_raises_on_empty():
    with pytest.raises(RuntimeError):
        _parse(_Resp(parsed=None, text=None))


def test_ingest_missing_file():
    with pytest.raises(FileNotFoundError):
        load_inputs(["khong_ton_tai.png"])


def test_ingest_unsupported_ext(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    with pytest.raises(ValueError):
        load_inputs([f])


def test_ingest_reads_image(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"\x89PNG\r\n")
    parts = load_inputs([f])
    assert parts == [(b"\x89PNG\r\n", "image/png")]
