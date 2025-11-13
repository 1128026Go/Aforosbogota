"""Check trayectorias structure"""
import pickle
from pathlib import Path

data_dir = Path('data') / 'dataset_f8144347'
pkl_file = data_dir / 'raw.pkl'

print(">> Cargando raw.pkl...")
raw_data = pickle.load(open(pkl_file, 'rb'))

trayectorias = raw_data['trayectorias']

print(f"Tipo de trayectorias: {type(trayectorias)}")

if isinstance(trayectorias, dict):
    keys = list(trayectorias.keys())
    print(f"\nTotal tracks: {len(keys)}")
    print(f"\nPrimeros 5 track_ids: {keys[:5]}")

    # Ver estructura de un track
    first_track_id = keys[0]
    first_track = trayectorias[first_track_id]

    print(f"\nEstructura del track {first_track_id}:")
    print(f"  Tipo: {type(first_track)}")
    if isinstance(first_track, dict):
        print(f"  Keys: {list(first_track.keys())}")
        for key in first_track.keys():
            val = first_track[key]
            if isinstance(val, list):
                print(f"    {key}: {len(val)} items")
            else:
                print(f"    {key}: {val}")
