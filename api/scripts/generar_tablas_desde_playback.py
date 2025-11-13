"""
Genera tablas RILSA CSV desde playback_events.json
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Añadir path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "yolo_carla_pipeline"))

from modules.rilsa_tablas import GeneradorTablasRILSA


def convertir_events_a_tracks(events_data: dict) -> list:
    """
    Convierte eventos de playback_events.json a formato de tracks para GeneradorTablasRILSA

    Args:
        events_data: Dict con key 'events' conteniendo lista de eventos

    Returns:
        Lista de dicts con formato: {track_id, class, movimiento_rilsa, origen, destino, first_frame, ...}
    """
    tracks = []

    for event in events_data.get('events', []):
        # Extraer información
        track_id = event.get('track_id', '')
        clase = event.get('class', 'unknown')
        mov_rilsa = event.get('mov_rilsa', 0)
        origen = event.get('origin_cardinal', '?')
        destino = event.get('dest_cardinal', '?')
        first_frame = event.get('frame_entry', 0)
        last_frame = event.get('frame_exit', 0)

        # Convertir código RILSA numérico a string formato esperado
        if mov_rilsa >= 101:
            mov_rilsa_str = f"10({mov_rilsa - 100})"  # 101 → "10(1)"
        elif mov_rilsa >= 91:
            mov_rilsa_str = f"9({mov_rilsa - 90})"    # 91 → "9(1)"
        else:
            mov_rilsa_str = str(mov_rilsa)             # 1-8 → "1"-"8"

        track = {
            'track_id': track_id,
            'class': clase,
            'cls': clase,  # Alias
            'movimiento_rilsa': mov_rilsa_str,
            'origen': origen,
            'destino': destino,
            'first_frame': first_frame,
            'last_frame': last_frame,
            'frame': first_frame,  # Para compatibilidad
        }

        tracks.append(track)

    return tracks


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_tablas_desde_playback.py <dataset_id>")
        sys.exit(1)

    dataset_id = sys.argv[1]

    # Paths
    data_dir = Path(__file__).parent.parent / "data" / dataset_id
    playback_file = data_dir / "playback_events.json"
    output_dir = data_dir / "entregables_rilsa"

    # Verificar que existe el archivo
    if not playback_file.exists():
        print(f"ERROR: No existe {playback_file}")
        sys.exit(1)

    print(f"Leyendo {playback_file}...")
    with open(playback_file, 'r', encoding='utf-8') as f:
        events_data = json.load(f)

    total_events = len(events_data.get('events', []))
    print(f"Total eventos: {total_events}")

    # Convertir a formato tracks
    print("Convirtiendo eventos a tracks...")
    tracks = convertir_events_a_tracks(events_data)

    # Filtrar solo vehículos para tablas (opcional, el generador ya filtra)
    vehiculares = [t for t in tracks if t['class'] not in ['person', 'peaton', 'pedestrian']]
    peatonales = [t for t in tracks if t['class'] in ['person', 'peaton', 'pedestrian']]

    print(f"  Tracks vehiculares: {len(vehiculares)}")
    print(f"  Tracks peatonales: {len(peatonales)}")

    # Crear generador RILSA
    # Usar fecha del primer evento si está disponible
    fecha_base = datetime(2025, 11, 10, 6, 0, 0)  # Default

    generador = GeneradorTablasRILSA(fps=30.0, fecha_base=fecha_base)

    # Generar y exportar tablas
    print(f"\nGenerando tablas RILSA en {output_dir}...")
    output_dir.mkdir(exist_ok=True)

    generador.exportar_tablas(tracks, str(output_dir))

    print(f"\n✓ Tablas RILSA generadas exitosamente en {output_dir}/")
    print(f"  - volumenes_15min_por_movimiento.csv")
    print(f"  - volumenes_por_movimiento.csv")
    print(f"  - resumen_por_acceso.csv")
    print(f"  - resumen_por_tipo_movimiento.csv")


if __name__ == "__main__":
    main()
