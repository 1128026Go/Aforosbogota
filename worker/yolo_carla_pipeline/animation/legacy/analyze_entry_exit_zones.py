"""
Análisis de Zonas de Entrada y Salida (Entry/Exit Analysis).

Identifica y visualiza las zonas más frecuentes donde los vehículos
entran y salen del campo de visión (puntos de acceso).
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class EntryExitAnalyzer:
    """Analizador de puntos de entrada y salida."""

    def __init__(self, combined_data_path: str):
        """Inicializa el analizador."""
        logger.info(f"Cargando datos desde: {combined_data_path}")

        with open(combined_data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.trajectories = self.data['trajectories']
        self.aforos = self.data['aforos']

        logger.info(f"  - Total trayectorias: {len(self.trajectories)}")
        logger.info(f"  - Total aforos: {len(self.aforos)}")

    def extract_entry_exit_points(self) -> Dict:
        """Extrae puntos de entrada y salida de todas las trayectorias."""
        entry_points = []
        exit_points = []

        entry_by_aforo = defaultdict(list)
        exit_by_aforo = defaultdict(list)

        entry_by_class = defaultdict(list)
        exit_by_class = defaultdict(list)

        logger.info("\nExtrayendo puntos de entrada y salida...")

        for traj in self.trajectories:
            positions = traj['positions']

            if len(positions) < 2:
                continue

            # Punto de entrada: primera posición
            entry_point = positions[0]
            entry_points.append(entry_point)

            # Punto de salida: última posición
            exit_point = positions[-1]
            exit_points.append(exit_point)

            # Por aforo
            aforo_id = traj.get('aforo_id', 'unknown')
            entry_by_aforo[aforo_id].append(entry_point)
            exit_by_aforo[aforo_id].append(exit_point)

            # Por clase
            clase = traj.get('clase', 'unknown')
            entry_by_class[clase].append(entry_point)
            exit_by_class[clase].append(exit_point)

        logger.info(f"  - Puntos de entrada extraídos: {len(entry_points)}")
        logger.info(f"  - Puntos de salida extraídos: {len(exit_points)}")

        return {
            'entry_points': entry_points,
            'exit_points': exit_points,
            'entry_by_aforo': dict(entry_by_aforo),
            'exit_by_aforo': dict(exit_by_aforo),
            'entry_by_class': dict(entry_by_class),
            'exit_by_class': dict(exit_by_class)
        }

    def calculate_grid_density(self, points: List[List[float]], grid_size: int = 50) -> Dict:
        """Calcula densidad en una cuadrícula."""
        if not points:
            return {}

        density_grid = defaultdict(int)

        for point in points:
            x, y = point
            grid_x = int(x // grid_size)
            grid_y = int(y // grid_size)
            grid_key = f"{grid_x},{grid_y}"
            density_grid[grid_key] += 1

        return dict(density_grid)

    def find_hotspots(self, density_grid: Dict, top_n: int = 10) -> List[Tuple]:
        """Identifica las zonas más calientes (hotspots)."""
        sorted_zones = sorted(density_grid.items(), key=lambda x: x[1], reverse=True)
        return sorted_zones[:top_n]

    def analyze(self, grid_size: int = 50) -> Dict:
        """Realiza análisis completo de entradas y salidas."""
        logger.info("\n" + "="*70)
        logger.info("ANÁLISIS DE ZONAS DE ENTRADA Y SALIDA")
        logger.info("="*70)

        # Extraer puntos
        points_data = self.extract_entry_exit_points()

        # Calcular densidades
        entry_density = self.calculate_grid_density(points_data['entry_points'], grid_size)
        exit_density = self.calculate_grid_density(points_data['exit_points'], grid_size)

        # Encontrar hotspots
        entry_hotspots = self.find_hotspots(entry_density, top_n=10)
        exit_hotspots = self.find_hotspots(exit_density, top_n=10)

        # Análisis por aforo
        aforo_stats = {}
        for aforo_id in points_data['entry_by_aforo'].keys():
            aforo_stats[aforo_id] = {
                'num_entries': len(points_data['entry_by_aforo'][aforo_id]),
                'num_exits': len(points_data['exit_by_aforo'][aforo_id]),
                'entry_hotspots': self.find_hotspots(
                    self.calculate_grid_density(points_data['entry_by_aforo'][aforo_id], grid_size),
                    top_n=5
                ),
                'exit_hotspots': self.find_hotspots(
                    self.calculate_grid_density(points_data['exit_by_aforo'][aforo_id], grid_size),
                    top_n=5
                )
            }

        # Análisis por clase
        class_stats = {}
        for clase in points_data['entry_by_class'].keys():
            class_stats[clase] = {
                'num_entries': len(points_data['entry_by_class'][clase]),
                'num_exits': len(points_data['exit_by_class'][clase])
            }

        logger.info("\n" + "="*70)
        logger.info("RESULTADOS DEL ANÁLISIS")
        logger.info("="*70)

        # Mostrar hotspots generales
        logger.info("\nTop 10 Zonas de ENTRADA más frecuentes:")
        for i, (zone, count) in enumerate(entry_hotspots, 1):
            grid_coords = zone.split(',')
            x_center = (int(grid_coords[0]) + 0.5) * grid_size
            y_center = (int(grid_coords[1]) + 0.5) * grid_size
            logger.info(f"  {i}. Zona ({x_center:.0f}, {y_center:.0f}) - {count} entradas")

        logger.info("\nTop 10 Zonas de SALIDA más frecuentes:")
        for i, (zone, count) in enumerate(exit_hotspots, 1):
            grid_coords = zone.split(',')
            x_center = (int(grid_coords[0]) + 0.5) * grid_size
            y_center = (int(grid_coords[1]) + 0.5) * grid_size
            logger.info(f"  {i}. Zona ({x_center:.0f}, {y_center:.0f}) - {count} salidas")

        # Mostrar por aforo
        logger.info("\nAnálisis por AFORO:")
        for aforo_id, stats in aforo_stats.items():
            aforo_info = next((a for a in self.aforos if a['id'] == aforo_id), None)
            nombre = aforo_info['nombre'] if aforo_info else aforo_id
            logger.info(f"\n  {nombre}:")
            logger.info(f"    - Total entradas: {stats['num_entries']}")
            logger.info(f"    - Total salidas: {stats['num_exits']}")
            logger.info(f"    - Top 3 zonas de entrada:")
            for i, (zone, count) in enumerate(stats['entry_hotspots'][:3], 1):
                logger.info(f"      {i}. {count} entradas")
            logger.info(f"    - Top 3 zonas de salida:")
            for i, (zone, count) in enumerate(stats['exit_hotspots'][:3], 1):
                logger.info(f"      {i}. {count} salidas")

        # Mostrar por clase
        logger.info("\nAnálisis por CLASE de vehículo:")
        for clase, stats in sorted(class_stats.items(), key=lambda x: x[1]['num_entries'], reverse=True):
            logger.info(f"  {clase.upper()}:")
            logger.info(f"    - Entradas: {stats['num_entries']}")
            logger.info(f"    - Salidas: {stats['num_exits']}")

        return {
            'points_data': points_data,
            'entry_density': entry_density,
            'exit_density': exit_density,
            'entry_hotspots': entry_hotspots,
            'exit_hotspots': exit_hotspots,
            'aforo_stats': aforo_stats,
            'class_stats': class_stats,
            'grid_size': grid_size
        }

    def save_analysis(self, analysis_results: Dict, output_path: str):
        """Guarda resultados del análisis en JSON."""
        # Convertir para JSON serializable
        output_data = {
            'entry_hotspots': [
                {'zone': zone, 'count': count, 'coordinates': self._zone_to_coords(zone, analysis_results['grid_size'])}
                for zone, count in analysis_results['entry_hotspots']
            ],
            'exit_hotspots': [
                {'zone': zone, 'count': count, 'coordinates': self._zone_to_coords(zone, analysis_results['grid_size'])}
                for zone, count in analysis_results['exit_hotspots']
            ],
            'aforo_stats': analysis_results['aforo_stats'],
            'class_stats': analysis_results['class_stats'],
            'grid_size': analysis_results['grid_size']
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\nOK - Análisis guardado en: {output_path}")

    def _zone_to_coords(self, zone: str, grid_size: int) -> List[float]:
        """Convierte coordenadas de zona a coordenadas centrales."""
        grid_coords = zone.split(',')
        x_center = (int(grid_coords[0]) + 0.5) * grid_size
        y_center = (int(grid_coords[1]) + 0.5) * grid_size
        return [x_center, y_center]


def main():
    if len(sys.argv) < 2:
        print("Uso: python analyze_entry_exit_zones.py <combined_aforos.json> [--output <analysis.json>] [--grid-size <num>]")
        print("\nOpciones:")
        print("  --output      Archivo de salida JSON (default: entry_exit_analysis.json)")
        print("  --grid-size   Tamaño de la cuadrícula en píxeles (default: 50)")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = "entry_exit_analysis.json"
    grid_size = 50

    if "--output" in sys.argv:
        output_file = sys.argv[sys.argv.index("--output") + 1]

    if "--grid-size" in sys.argv:
        grid_size = int(sys.argv[sys.argv.index("--grid-size") + 1])

    print("="*70)
    print("ANALIZADOR DE ZONAS DE ENTRADA Y SALIDA")
    print("="*70)

    # Análisis
    analyzer = EntryExitAnalyzer(input_file)
    results = analyzer.analyze(grid_size=grid_size)
    analyzer.save_analysis(results, output_file)

    print("\n" + "="*70)
    print("ANÁLISIS COMPLETO")
    print("="*70)


if __name__ == "__main__":
    main()
