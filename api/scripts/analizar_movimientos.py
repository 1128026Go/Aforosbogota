import json
from pathlib import Path
from collections import Counter

# Leer datos
script_dir = Path(__file__).parent.parent
data_file = script_dir / "data" / "dataset_f8144347" / "playback_events.json"

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Analizar patrones
movimientos = []
for e in data['events']:
    origen = e.get('origin_cardinal', '?')
    destino = e.get('dest_cardinal', '?')
    mov = e.get('mov_rilsa', '?')
    movimientos.append((origen, mov, destino))

# Contar
counter = Counter(movimientos)

print('Top 30 combinaciones (Origen, Mov_RILSA, Destino):')
print('-' * 60)
for (origen, mov, destino), count in counter.most_common(30):
    print(f'{origen} > {destino} (Mov {mov}): {count} eventos')
