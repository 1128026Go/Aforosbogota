"""
Persistencia de accesos cardinales y mapa RILSA asociados a un dataset.
"""
from __future__ import annotations

import json
from typing import Dict, List

from api.models.config import AccessConfig
from . import rilsa_mapping


def persist_cardinals_and_rilsa(dataset_id: str, accesses: List[AccessConfig]) -> None:
    """
    Serializa `cardinals.json` y `rilsa_map.json` en data/<dataset_id>/.
    """
    from api.routers.datasets import _dataset_dir  # import diferido para evitar ciclos

    dataset_dir = _dataset_dir(dataset_id)
    cardinals_file = dataset_dir / "cardinals.json"
    rilsa_file = dataset_dir / "rilsa_map.json"

    raw_accesses: List[Dict] = []
    for access in accesses:
        centroid = access.centroid if access.centroid else None
        cx = float(centroid[0]) if centroid else 0.0
        cy = float(centroid[1]) if centroid else 0.0
        polygon = [
            [float(point[0]), float(point[1])]
            for point in (access.polygon or [])
        ]

        raw_accesses.append(
            {
                "id": access.id,
                "cardinal": access.cardinal,
                "x": cx,
                "y": cy,
                "count": len(polygon),
                "polygon": polygon,
            }
        )

    # Persistir accesos
    cardinals_file.write_text(
        json.dumps(raw_accesses, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Generar mapa RILSA y persistirlo
    rilsa_map = rilsa_mapping.build_rilsa_rule_map(raw_accesses)
    rilsa_file.write_text(
        json.dumps(rilsa_map, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

