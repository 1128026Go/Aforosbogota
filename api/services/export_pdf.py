"""
Generación de reportes PDF a partir de HTML renderizado.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader


def render_html_report(
    templates_dir: Path,
    context: Dict[str, object],
) -> str:
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template("report.html")
    return template.render(**context)


def export_pdf(html: str, out_path: Path) -> None:
    try:
        from weasyprint import HTML
    except ImportError:
        out_path.with_suffix(".html").write_text(html, encoding="utf-8")
        raise RuntimeError("WeasyPrint no está instalado en el entorno.")
    HTML(string=html).write_pdf(str(out_path))

