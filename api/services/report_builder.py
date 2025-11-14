"""
Construcción de tablas estructuradas tipo hoja de cálculo.
"""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

def _empty_row(interval_start: int, interval_end: int) -> Dict:
    return {
        "interval_start": interval_start,
        "interval_end": interval_end,
        "autos": 0,
        "buses": 0,
        "camiones": 0,
        "motos": 0,
        "bicis": 0,
        "peatones": 0,
        "total": 0,
    }


def build_volume_tables(counts_df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """
    Genera dict con:
      - totals: lista de filas agregadas por intervalo.
      - movements: dict rilsa_code -> filas del movimiento.
    """
    if counts_df.empty:
        return {"totals": [], "movements": {}}

    totals: Dict[int, Dict] = {}
    movements: Dict[str, Dict[int, Dict]] = {}

    for _, row in counts_df.iterrows():
        interval_start = int(row["interval_start"])
        interval_end = int(row["interval_end"])
        rilsa_code = str(row["rilsa_code"])
        vehicle_class = str(row["vehicle_class"])
        count = int(row["count"])

        if interval_start not in totals:
            totals[interval_start] = _empty_row(interval_start, interval_end)
        total_row = totals[interval_start]

        column_map = {
            "auto": "autos",
            "bus": "buses",
            "camion": "camiones",
            "moto": "motos",
            "bici": "bicis",
            "peaton": "peatones",
        }
        column = column_map.get(vehicle_class)
        if column:
            total_row[column] += count
            total_row["total"] += count

        if rilsa_code not in movements:
            movements[rilsa_code] = {}
        movement_rows = movements[rilsa_code]
        if interval_start not in movement_rows:
            movement_rows[interval_start] = _empty_row(interval_start, interval_end)
        movement_row = movement_rows[interval_start]
        if column:
            movement_row[column] += count
            movement_row["total"] += count

    totals_list = [totals[idx] for idx in sorted(totals.keys())]
    movement_tables = {
        code: [movement_rows[idx] for idx in sorted(movement_rows.keys())]
        for code, movement_rows in movements.items()
    }

    return {"totals": totals_list, "movements": movement_tables}

