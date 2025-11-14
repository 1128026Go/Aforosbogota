"""
Detección de maniobras indebidas según la configuración del dataset.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List

import pandas as pd

from api.models.config import ForbiddenMovement


def summarize_violations(
    movements_df: pd.DataFrame, forbidden_movements: List[ForbiddenMovement]
) -> Dict[str, object]:
    """Genera un resumen de violaciones por código RILSA prohibido."""
    if movements_df.empty or not forbidden_movements:
        return {"total_violations": 0, "by_movement": []}

    forbidden_index = {fm.rilsa_code: fm.description or "" for fm in forbidden_movements}
    counter = Counter()

    for rilsa_code in movements_df["rilsa_code"].astype(str):
        if rilsa_code in forbidden_index:
            counter[rilsa_code] += 1

    summaries = [
        {
            "rilsa_code": code,
            "description": forbidden_index.get(code, ""),
            "count": count,
        }
        for code, count in counter.items()
    ]

    summaries.sort(key=lambda item: item["count"], reverse=True)

    return {
        "total_violations": sum(counter.values()),
        "by_movement": summaries,
    }

