"""Smoke test CLI: patch extract (khỏi cần key), chạy --no-png --no-pdf (khỏi cần browser)."""
from typer.testing import CliRunner

import loban.cli as cli
from loban.models import Dimension, ExtractionResult

runner = CliRunner()


def _fake_extract(images, note="", **kw):
    return ExtractionResult(dimensions=[
        Dimension(label="Rộng mộ", category="mo", kind="phu_bi", value_mm=870, confidence="cao"),
        Dimension(label="Mờ", category="cong", kind="thong_thuy", value_mm=None, confidence="chua_xac_dinh"),
    ])


def test_cli_run_analysis_only(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "extract", _fake_extract)
    img = tmp_path / "banve.png"
    img.write_bytes(b"\x89PNG\r\n")

    result = runner.invoke(cli.app, [
        str(img), "--ho-so", "HS01", "--khach-hang", "Ông A",
        "--out", str(tmp_path / "out"), "--no-png", "--no-pdf",
    ])
    assert result.exit_code == 0, result.output
    analysis = tmp_path / "out" / "HS01" / "analysis.json"
    assert analysis.exists()
    assert "cần xác nhận: Mờ" in result.output
