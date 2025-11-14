"""
Exportación de tablas de volúmenes a Excel multi-hoja.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


def export_volumes_to_excel(
    out_path: Path,
    totals: List[Dict],
    movements: Dict[str, List[Dict]],
) -> None:
    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        if totals:
            pd.DataFrame(totals).to_excel(writer, sheet_name="Totales", index=False)
        for rilsa_code, rows in movements.items():
            sheet = f"Mov_{rilsa_code}"[:31]
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet, index=False)

