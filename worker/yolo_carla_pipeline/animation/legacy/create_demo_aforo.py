"""
Script rápido para crear un aforo de demostración duplicando datos existentes.
Útil para demostrar la funcionalidad multi-aforo sin esperar procesamiento largo.
"""

import json
import sys
from pathlib import Path

def create_demo_aforo(source_json, output_json, sample_size=500):
    """Crea un aforo de demostración tomando una muestra del source."""

    print(f"Creando aforo de demostracion desde: {source_json}")

    with open(source_json, 'r') as f:
        trajectories = json.load(f)

    print(f"  - Trayectorias originales: {len(trajectories)}")

    # Tomar muestra
    if len(trajectories) > sample_size:
        step = len(trajectories) // sample_size
        trajectories = trajectories[::step]

    print(f"  - Trayectorias de muestra: {len(trajectories)}")

    # Guardar
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(trajectories, f, ensure_ascii=False, indent=2)

    print(f"OK - Aforo de demostracion guardado en: {output_json}")
    print(f"  Tamaño: {output_path.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python create_demo_aforo.py <source.json> <output.json> [sample_size]")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2]
    sample_size = int(sys.argv[3]) if len(sys.argv) > 3 else 500

    create_demo_aforo(source, output, sample_size)
