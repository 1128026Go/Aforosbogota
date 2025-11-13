"""
Script para debuggear la segmentación de trayectorias
Analiza cuántos cruces de accesos se detectan por track
"""
import json
import pickle
from pathlib import Path

def point_in_polygon(point, polygon):
    """Ray casting algorithm para determinar si un punto está dentro de un polígono"""
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def debug_track_crossings(dataset_id='dataset_f8144347', track_id=77):
    """Analiza los cruces de accesos para un track específico"""

    data_dir = Path('data') / dataset_id
    pkl_file = data_dir / 'raw.pkl'
    cardinals_file = data_dir / 'cardinals.json'

    print(f">> Analizando track {track_id}...")

    # Cargar datos
    raw_data = pickle.load(open(pkl_file, 'rb'))
    cardinals = json.load(open(cardinals_file, encoding='utf-8'))

    tracks = raw_data['trayectorias']
    accesses = cardinals.get('accesses', [])

    # Encontrar el track
    track = None
    for t in tracks:
        if t['track_id'] == track_id:
            track = t
            break

    if not track:
        print(f"Track {track_id} no encontrado")
        return

    positions = track['positions']
    frames = track['frames']

    print(f"\nTrack {track_id}:")
    print(f"  Total posiciones: {len(positions)}")
    print(f"  Frames: {frames[0]} - {frames[-1]}")
    print(f"  Clase: {track['class']}")

    # Detectar cruces de accesos
    print(f"\n>> Detección de cruces de accesos:")
    access_crossings = []

    for i, pos in enumerate(positions):
        x, y = float(pos[0]), float(pos[1])

        for access in accesses:
            in_access = False
            polygon = access.get('polygon', [])

            if polygon and len(polygon) >= 3:
                polygon_tuples = [
                    (p['x'], p['y']) if isinstance(p, dict) else tuple(p) if isinstance(p, list) else p
                    for p in polygon
                ]
                in_access = point_in_polygon((x, y), polygon_tuples)

            if in_access:
                access_crossings.append({
                    'frame_idx': i,
                    'frame': frames[i],
                    'access_id': access['id'],
                    'cardinal': access.get('cardinal_official', access.get('cardinal')),
                    'position': (x, y)
                })
                break

    print(f"  Total cruces detectados: {len(access_crossings)}")

    if len(access_crossings) > 0:
        print(f"\n  Detalles de cruces:")
        for i, crossing in enumerate(access_crossings):
            print(f"    [{i}] Frame {crossing['frame']} (idx={crossing['frame_idx']}): "
                  f"{crossing['cardinal']} (access_id={crossing['access_id']}) "
                  f"pos=({crossing['position'][0]:.1f}, {crossing['position'][1]:.1f})")

        # Detectar cambios de acceso
        changes = []
        for i in range(1, len(access_crossings)):
            if access_crossings[i]['access_id'] != access_crossings[i-1]['access_id']:
                changes.append(i)

        print(f"\n  Cambios de acceso detectados: {len(changes)}")
        for idx in changes:
            prev = access_crossings[idx-1]
            curr = access_crossings[idx]
            print(f"    Frame {prev['frame']} ({prev['cardinal']}) -> Frame {curr['frame']} ({curr['cardinal']})")
    else:
        print(f"  ⚠️ NO se detectaron cruces de accesos!")
        print(f"  Primeras 5 posiciones: {positions[:5]}")
        print(f"  Últimas 5 posiciones: {positions[-5:]}")

    # Mostrar configuración de accesos
    print(f"\n>> Configuración de accesos:")
    for access in accesses:
        cardinal = access.get('cardinal_official', access.get('cardinal'))
        polygon = access.get('polygon', [])
        print(f"  {cardinal} (id={access['id']}): {len(polygon)} puntos en polígono")

def analyze_all_tracks(dataset_id='dataset_f8144347'):
    """Analiza cuántos cruces detecta cada track"""

    data_dir = Path('data') / dataset_id
    pkl_file = data_dir / 'raw.pkl'
    cardinals_file = data_dir / 'cardinals.json'

    print(f">> Analizando todos los tracks...")

    raw_data = pickle.load(open(pkl_file, 'rb'))
    cardinals = json.load(open(cardinals_file, encoding='utf-8'))

    tracks = raw_data['trayectorias']
    accesses = cardinals.get('accesses', [])

    stats = {
        'no_crossings': 0,
        'single_crossing': 0,
        'multiple_same_access': 0,
        'multiple_different_access': 0
    }

    tracks_with_segments = []

    for track in tracks:
        positions = track['positions']
        frames = track['frames']

        # Detectar cruces
        access_crossings = []
        for i, pos in enumerate(positions):
            x, y = float(pos[0]), float(pos[1])

            for access in accesses:
                in_access = False
                polygon = access.get('polygon', [])

                if polygon and len(polygon) >= 3:
                    polygon_tuples = [
                        (p['x'], p['y']) if isinstance(p, dict) else tuple(p) if isinstance(p, list) else p
                        for p in polygon
                    ]
                    in_access = point_in_polygon((x, y), polygon_tuples)

                if in_access:
                    access_crossings.append(access['id'])
                    break

        if len(access_crossings) == 0:
            stats['no_crossings'] += 1
        elif len(access_crossings) == 1:
            stats['single_crossing'] += 1
        else:
            # Verificar si hay cambios de acceso
            unique_accesses = set(access_crossings)
            if len(unique_accesses) == 1:
                stats['multiple_same_access'] += 1
            else:
                stats['multiple_different_access'] += 1
                tracks_with_segments.append({
                    'track_id': track['track_id'],
                    'accesses': list(unique_accesses),
                    'crossings': len(access_crossings)
                })

    print(f"\n>> RESULTADOS:")
    print(f"  Total tracks: {len(tracks)}")
    print(f"  Sin cruces detectados: {stats['no_crossings']}")
    print(f"  Un solo cruce: {stats['single_crossing']}")
    print(f"  Múltiples cruces (mismo acceso): {stats['multiple_same_access']}")
    print(f"  Múltiples cruces (diferentes accesos): {stats['multiple_different_access']}")

    if tracks_with_segments:
        print(f"\n>> Tracks con posible segmentación ({len(tracks_with_segments)} primeros 10):")
        for t in tracks_with_segments[:10]:
            print(f"  Track {t['track_id']}: {t['crossings']} cruces en {len(t['accesses'])} accesos diferentes")

if __name__ == '__main__':
    # Analizar un track específico (el primero que vimos: track_77)
    debug_track_crossings(track_id=77)

    print("\n" + "="*80 + "\n")

    # Analizar todos los tracks
    analyze_all_tracks()
