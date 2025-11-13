"""
Script manual para procesar playback y capturar errores
"""
import json
import sys
from pathlib import Path
import numpy as np
from services.trajectory_processor import TrajectoryProcessor

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

try:
    print("Iniciando procesamiento...")
    tp = TrajectoryProcessor(Path('data'))
    result = tp.process_dataset('dataset_f8144347')

    print(f"\nProcesamiento exitoso: {result['metadata']['total_events']} eventos")

    # Guardar con UTF-8
    playback_file = Path('data/dataset_f8144347/playback_events.json')
    with open(playback_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)

    print(f"Archivo guardado: {playback_file}")
    print("EXITO!")

except Exception as e:
    print(f"\nERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
