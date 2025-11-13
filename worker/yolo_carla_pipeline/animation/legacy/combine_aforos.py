"""
Sistema de Integración de Múltiples Aforos.

Combina múltiples archivos JSON de trayectorias en un solo lienzo,
aplicando offsets espaciales para cada aforo.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# Configuración de colores y emojis por clase
COLOR_MAP = {
    'car': '#3498db',
    'truck': '#e74c3c',
    'bus': '#9b59b6',
    'motorcycle': '#f39c12',
    'bicycle': '#2ecc71',
    'person': '#1abc9c',
    'unknown': '#95a5a6'
}

EMOJI_MAP = {
    'car': '🚗',
    'truck': '🚚',
    'bus': '🚌',
    'motorcycle': '🏍️',
    'bicycle': '🚴',
    'person': '🚶',
    'unknown': '⚫'
}


class AforoIntegrator:
    """Integrador de múltiples aforos en un solo canvas."""

    def __init__(self, config_path: str):
        """Inicializa el integrador con la configuración."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.aforos = self.config['aforos']
        self.base_path = Path(config_path).parent.parent

        logger.info(f"Configuración cargada: {len(self.aforos)} aforos definidos")

    def load_aforo_data(self, aforo_config: Dict) -> List[Dict]:
        """Carga datos de un aforo específico."""
        tracks_file = self.base_path / aforo_config['tracks_file']

        if not tracks_file.exists():
            logger.warning(f"Archivo no encontrado: {tracks_file}")
            return []

        try:
            with open(tracks_file, 'r', encoding='utf-8') as f:
                trajectories = json.load(f)

            logger.info(f"  - {aforo_config['nombre']}: {len(trajectories)} trayectorias")
            return trajectories

        except Exception as e:
            logger.error(f"Error cargando {tracks_file}: {e}")
            return []

    def calculate_cardinal_from_position(self, x: float, y: float, bounds: Dict) -> str:
        """Calcula punto cardinal basado en posición relativa."""
        center_x = (bounds['min_x'] + bounds['max_x']) / 2
        center_y = (bounds['min_y'] + bounds['max_y']) / 2

        # Determinar cuadrante
        is_north = y < center_y
        is_east = x > center_x

        # Asignar cardinal basado en el borde más cercano
        dist_to_top = abs(y - bounds['min_y'])
        dist_to_bottom = abs(y - bounds['max_y'])
        dist_to_left = abs(x - bounds['min_x'])
        dist_to_right = abs(x - bounds['max_x'])

        min_dist = min(dist_to_top, dist_to_bottom, dist_to_left, dist_to_right)

        if min_dist == dist_to_top:
            return 'N'
        elif min_dist == dist_to_bottom:
            return 'S'
        elif min_dist == dist_to_left:
            return 'O'
        else:
            return 'E'

    def apply_offset(self, trajectories: List[Dict], offset_x: float, offset_y: float, aforo_id: str) -> List[Dict]:
        """Aplica offset espacial a las trayectorias de un aforo."""
        # Calcular bounds para determinar puntos cardinales
        all_positions = []
        for traj in trajectories:
            all_positions.extend(traj['positions'])

        if all_positions:
            xs = [p[0] for p in all_positions]
            ys = [p[1] for p in all_positions]
            bounds = {
                'min_x': min(xs),
                'max_x': max(xs),
                'min_y': min(ys),
                'max_y': max(ys)
            }
        else:
            bounds = {'min_x': 0, 'max_x': 1920, 'min_y': 0, 'max_y': 1080}

        offset_trajectories = []

        for traj in trajectories:
            # Copiar trayectoria
            new_traj = traj.copy()

            # Aplicar offset a todas las posiciones
            new_positions = []
            for pos in traj['positions']:
                new_pos = [pos[0] + offset_x, pos[1] + offset_y]
                new_positions.append(new_pos)

            new_traj['positions'] = new_positions

            # Calcular origin y destination cardinales
            if traj['positions']:
                first_pos = traj['positions'][0]
                last_pos = traj['positions'][-1]

                new_traj['origin_cardinal'] = self.calculate_cardinal_from_position(
                    first_pos[0], first_pos[1], bounds
                )
                new_traj['dest_cardinal'] = self.calculate_cardinal_from_position(
                    last_pos[0], last_pos[1], bounds
                )
            else:
                new_traj['origin_cardinal'] = 'N'
                new_traj['dest_cardinal'] = 'S'

            # Agregar metadatos del aforo
            new_traj['aforo_id'] = aforo_id
            new_traj['aforo_offset'] = [offset_x, offset_y]

            # Hacer track_id único globalmente
            new_traj['track_id_original'] = new_traj['track_id']
            new_traj['track_id'] = f"{aforo_id}_{new_traj['track_id']}"

            # Agregar color y emoji según la clase
            clase = new_traj.get('clase', 'unknown')
            new_traj['color'] = COLOR_MAP.get(clase, COLOR_MAP['unknown'])
            new_traj['emoji'] = EMOJI_MAP.get(clase, EMOJI_MAP['unknown'])

            offset_trajectories.append(new_traj)

        return offset_trajectories

    def combine_aforos(self, sample_size: int = 1000) -> Dict:
        """Combina todos los aforos activos en un solo conjunto de datos."""
        logger.info("\nCombinando aforos activos...")

        all_trajectories = []
        aforos_info = []

        for aforo in self.aforos:
            if not aforo['activo']:
                logger.info(f"Saltando aforo inactivo: {aforo['nombre']}")
                continue

            logger.info(f"\nProcesando: {aforo['nombre']}")

            # Cargar datos
            trajectories = self.load_aforo_data(aforo)

            if not trajectories:
                continue

            # Aplicar muestreo si hay muchas trayectorias
            if len(trajectories) > sample_size:
                step = len(trajectories) // sample_size
                trajectories = trajectories[::step]
                logger.info(f"  - Muestreado: {len(trajectories)} trayectorias")

            # Aplicar offset
            offset_trajectories = self.apply_offset(
                trajectories,
                aforo['offset_x'],
                aforo['offset_y'],
                aforo['id']
            )

            all_trajectories.extend(offset_trajectories)

            # Guardar info del aforo
            aforos_info.append({
                'id': aforo['id'],
                'nombre': aforo['nombre'],
                'offset_x': aforo['offset_x'],
                'offset_y': aforo['offset_y'],
                'color_tema': aforo['color_tema'],
                'num_trayectorias': len(offset_trajectories)
            })

        logger.info(f"\n✓ Total combinado: {len(all_trajectories)} trayectorias de {len(aforos_info)} aforos")

        return {
            'trajectories': all_trajectories,
            'aforos': aforos_info,
            'metadata': {
                'total_aforos': len(aforos_info),
                'total_trayectorias': len(all_trajectories)
            }
        }

    def save_combined(self, output_path: str, sample_size: int = 1000):
        """Combina y guarda los datos integrados."""
        combined_data = self.combine_aforos(sample_size)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)

        file_size = output_file.stat().st_size / (1024 * 1024)
        logger.info(f"\n✓ Datos combinados guardados en: {output_path}")
        logger.info(f"  Tamaño: {file_size:.2f} MB")

        return combined_data


def main():
    if len(sys.argv) < 2:
        print("Uso: python combine_aforos.py [--output <archivo.json>] [--sample-size <num>]")
        print("\nOpciones:")
        print("  --output       Archivo de salida (default: combined_aforos.json)")
        print("  --sample-size  Número máximo de trayectorias por aforo (default: 1000)")
        sys.exit(1)

    # Argumentos
    output_path = "combined_aforos.json"
    sample_size = 1000

    if "--output" in sys.argv:
        output_path = sys.argv[sys.argv.index("--output") + 1]

    if "--sample-size" in sys.argv:
        sample_size = int(sys.argv[sys.argv.index("--sample-size") + 1])

    print("="*70)
    print("INTEGRADOR DE MULTIPLES AFOROS")
    print("="*70)

    # Ruta de configuración
    config_path = Path(__file__).parent.parent / "config" / "aforos_config.json"

    if not config_path.exists():
        logger.error(f"Archivo de configuración no encontrado: {config_path}")
        sys.exit(1)

    # Integrar
    integrator = AforoIntegrator(str(config_path))
    combined_data = integrator.save_combined(output_path, sample_size)

    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE INTEGRACIÓN")
    print("="*70)
    for aforo_info in combined_data['aforos']:
        print(f"  • {aforo_info['nombre']}")
        print(f"    - ID: {aforo_info['id']}")
        print(f"    - Offset: ({aforo_info['offset_x']}, {aforo_info['offset_y']})")
        print(f"    - Trayectorias: {aforo_info['num_trayectorias']}")
        print()

    print(f"Total: {combined_data['metadata']['total_trayectorias']} trayectorias")
    print(f"Aforos activos: {combined_data['metadata']['total_aforos']}")
    print("="*70)


if __name__ == "__main__":
    main()
