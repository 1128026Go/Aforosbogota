"""
Generación de reportes PDF a partir de HTML renderizado.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader


def render_html_report(
    templates_dir: Path,
    dataset_id: str,
    interval_minutes: int,
    totals: List[Dict],
    movements: Dict[str, List[Dict]],
    speed_summary: Dict,
    conflicts_summary: Dict,
) -> str:
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template("report.html")
    return template.render(
        dataset_id=dataset_id,
        interval_minutes=interval_minutes,
        totals=totals,
        movements=movements,
        speed_summary=speed_summary,
        conflicts_summary=conflicts_summary,
    )


def export_pdf(html: str, out_path: Path) -> None:
    try:
        from weasyprint import HTML
    except ImportError:
        out_path.with_suffix(".html").write_text(html, encoding="utf-8")
        raise RuntimeError("WeasyPrint no está instalado en el entorno.")
    HTML(string=html).write_pdf(str(out_path))

