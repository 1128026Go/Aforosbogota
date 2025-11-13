"""
Servicio de gestión de puntos cardinales
"""

import json
from pathlib import Path
from typing import Optional, Dict


class CardinalService:
    """Gestión de configuración de puntos cardinales"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def save_cardinals(self, dataset_id: str, config: Dict) -> None:
        """Guardar configuración de cardinales"""
        dataset_dir = self.data_dir / dataset_id
        dataset_dir.mkdir(exist_ok=True)

        cardinals_file = dataset_dir / "cardinals.json"
        cardinals_file.write_text(json.dumps(config, indent=2))

    def load_cardinals(self, dataset_id: str) -> Optional[Dict]:
        """Cargar configuración de cardinales"""
        cardinals_file = self.data_dir / dataset_id / "cardinals.json"

        if not cardinals_file.exists():
            return None

        return json.loads(cardinals_file.read_text())

    def save_rilsa_map(self, dataset_id: str, rilsa_map: Dict) -> None:
        """Guardar mapa de movimientos RILSA"""
        dataset_dir = self.data_dir / dataset_id
        dataset_dir.mkdir(exist_ok=True)

        rilsa_file = dataset_dir / "rilsa_map.json"
        rilsa_file.write_text(json.dumps(rilsa_map, indent=2))

    def load_rilsa_map(self, dataset_id: str) -> Optional[Dict]:
        """Cargar mapa de movimientos RILSA"""
        rilsa_file = self.data_dir / dataset_id / "rilsa_map.json"

        if not rilsa_file.exists():
            return None

        return json.loads(rilsa_file.read_text())
