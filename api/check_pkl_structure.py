"""Quick script to check raw.pkl structure"""
import pickle
from pathlib import Path

data_dir = Path('data') / 'dataset_f8144347'
pkl_file = data_dir / 'raw.pkl'

print(">> Cargando raw.pkl...")
raw_data = pickle.load(open(pkl_file, 'rb'))

print(f"\nTipo: {type(raw_data)}")
print(f"\nKeys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'No es dict'}")

if isinstance(raw_data, dict):
    for key in raw_data.keys():
        val = raw_data[key]
        if isinstance(val, list):
            print(f"\n{key}: {len(val)} items (type: {type(val[0]) if val else 'empty'})")
            if val and isinstance(val[0], dict):
                print(f"  Keys del primer item: {list(val[0].keys())}")
        else:
            print(f"\n{key}: {type(val)}")
