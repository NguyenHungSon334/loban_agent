"""CLI ghép chuỗi: ingest -> extract -> pipeline -> render (plan mục 2, P7).

    loban run ban_ve.png --ho-so HS01 --khach-hang "Ông A"
"""
from __future__ import annotations

from pathlib import Path

import typer

from .extract import extract
from .ingest import load_inputs
from .models import Profile
from .pipeline import build_report
from .render.analysis_json import write_analysis
from .render.png import write_png
from .render.pdf_report import write_pdf

app = typer.Typer(add_completion=False, help="Agent Lỗ Ban — đối chiếu kích thước bản vẽ.")


@app.command()
def run(
    inputs: list[Path] = typer.Argument(..., help="Ảnh/PDF bản vẽ"),
    ho_so: str = typer.Option(..., "--ho-so", help="Mã hồ sơ"),
    khach_hang: str = typer.Option(None, "--khach-hang"),
    dia_diem: str = typer.Option(None, "--dia-diem"),
    huong_cong: str = typer.Option(None, "--huong-cong"),
    vat_lieu: str = typer.Option(None, "--vat-lieu"),
    note: str = typer.Option("", "--note", help="Ghi chú/thông số nhân viên nhập"),
    out: Path = typer.Option(Path("output"), "--out"),
    light: bool = typer.Option(False, "--light", help="Dùng model Gemini flash (rẻ)"),
    png: bool = typer.Option(True, "--png/--no-png"),
    pdf: bool = typer.Option(True, "--pdf/--no-pdf"),
) -> None:
    images = load_inputs(inputs)
    extraction = extract(images, note, light=light)
    profile = Profile(
        ho_so=ho_so, khach_hang=khach_hang, dia_diem=dia_diem,
        huong_cong=huong_cong, vat_lieu=vat_lieu,
    )
    report = build_report(extraction, profile)
    out_dir = out / ho_so

    f = write_analysis(report, out_dir)
    typer.echo(f"analysis: {f}")

    drawing = images[0][0] if images else None   # bytes ảnh bản vẽ đầu tiên
    if png:
        for p in write_png(report, out_dir, drawing):
            typer.echo(f"png: {p}")
    if pdf:
        typer.echo(f"pdf: {write_pdf(report, out_dir, drawing)}")

    if report.need_confirm:
        typer.echo(f"⚠ cần xác nhận: {', '.join(report.need_confirm)}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
