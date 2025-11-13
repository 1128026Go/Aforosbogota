"""
Script para debuggear la segmentación de trayectorias
Analiza cuántos cruces de accesos se detectan por track usando playback_events.json
"""
import json
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

def debug_track(dataset_id='dataset_f8144347', track_id=77):
    """Analiza los cruces de accesos para un track específico"""

    data_dir = Path('data') / dataset_id
    playback_file = data_dir / 'playback_events.json'
    cardinals_file = data_dir / 'cardinals.json'

    print(f">> Analizando track {track_id}...")

    # Cargar datos
    playback = json.load(open(playback_file, encoding='utf-8'))
    cardinals = json.load(open(cardinals_file, encoding='utf-8'))

    events = playback['events']
    accesses = cardinals.get('accesses', [])

    # Encontrar el evento
    event = None
    for e in events:
        if e['track_id'] == track_id:
            event = e
            break

    if not event:
        print(f"  Track {track_id} no encontrado en playback_events.json")
        print(f"  Primer track disponible: {events[0]['track_id'] if events else 'ninguno'}")
        return

    positions = event['positions']

    print(f"\nTrack {track_id}:")
    print(f"  Total posiciones: {len(positions)}")
    print(f"  Clase: {event['class']}")
    print(f"  Movimiento reportado: {event.get('origin')} -> {event.get('destination')}")
    print(f"  Frames: {event.get('frame_entry', '?')} - {event.get('frame_exit', '?')}")

    # Detectar cruces de accesos a lo largo de toda la trayectoria
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
                    'pos_idx': i,
                    'access_id': access['id'],
                    'cardinal': access.get('cardinal_official', access.get('cardinal')),
                    'position': (x, y)
                })
                break  # Solo un acceso por posición

    print(f"  Total cruces detectados: {len(access_crossings)}")

    if len(access_crossings) > 0:
        print(f"\n  Detalles de cruces (primeros 20):")
        for i, crossing in enumerate(access_crossings[:20]):
            print(f"    [{i}] Pos {crossing['pos_idx']}/{len(positions)}: "
                  f"{crossing['cardinal']} (access_id={crossing['access_id']}) "
                  f"pos=({crossing['position'][0]:.1f}, {crossing['position'][1]:.1f})")

        if len(access_crossings) > 20:
            print(f"  ... y {len(access_crossings) - 20} cruces más")

        # Detectar cambios de acceso
        print(f"\n  >> Análisis de cambios de acceso:")
        current_access_id = None
        segments_detected = 0

        for crossing in access_crossings:
            if current_access_id is None:
                current_access_id = crossing['access_id']
                print(f"    Entrada inicial: {crossing['cardinal']} (pos {crossing['pos_idx']})")
            elif crossing['access_id'] != current_access_id:
                segments_detected += 1
                print(f"    CAMBIO #{segments_detected}: pos {crossing['pos_idx']} - "
                      f"Salida de {[a for a in accesses if a['id']==current_access_id][0].get('cardinal_official', '?')} → "
                      f"Entrada a {crossing['cardinal']}")
                current_access_id = crossing['access_id']

        print(f"\n  Total cambios de acceso detectados: {segments_detected}")
        print(f"  Total segmentos que deberían generarse: {segments_detected + 1}")

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
    """Analiza cuántos cruces detecta cada track en playback"""

    data_dir = Path('data') / dataset_id
    playback_file = data_dir / 'playback_events.json'
    cardinals_file = data_dir / 'cardinals.json'

    print(f">> Analizando todos los tracks en playback...")

    playback = json.load(open(playback_file, encoding='utf-8'))
    cardinals = json.load(open(cardinals_file, encoding='utf-8'))

    events = playback['events']
    accesses = cardinals.get('accesses', [])

    stats = {
        'no_crossings': 0,
        'single_access_only': 0,  # Solo detectado en un acceso (todo el recorrido en ese acceso)
        'multiple_same_access': 0,  # Detectado en múltiples posiciones pero mismo acceso
        'multiple_different_accesses': 0  # Detectado en múltiples accesos (cambios de acceso)
    }

    tracks_with_segments = []

    for event in events:
        positions = event['positions']

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
            stats['single_access_only'] += 1
        else:
            # Verificar si hay cambios de acceso
            unique_accesses = set(access_crossings)
            if len(unique_accesses) == 1:
                stats['multiple_same_access'] += 1
            else:
                # Contar cuántos cambios hay
                changes = 0
                prev_access = None
                for access_id in access_crossings:
                    if prev_access and access_id != prev_access:
                        changes += 1
                    prev_access = access_id

                stats['multiple_different_accesses'] += 1
                tracks_with_segments.append({
                    'track_id': event['track_id'],
                    'movement': f"{event.get('origin', '?')} -> {event.get('destination', '?')}",
                    'unique_accesses': len(unique_accesses),
                    'crossings': len(access_crossings),
                    'changes': changes,
                    'expected_segments': changes + 1
                })

    print(f"\n>> RESULTADOS:")
    print(f"  Total eventos en playback: {len(events)}")
    print(f"  Sin cruces detectados: {stats['no_crossings']}")
    print(f"  Un solo cruce: {stats['single_access_only']}")
    print(f"  Múltiples cruces (mismo acceso): {stats['multiple_same_access']}")
    print(f"  Múltiples cruces (diferentes accesos): {stats['multiple_different_accesses']}")

    if tracks_with_segments:
        print(f"\n>> Tracks CON segmentación potencial ({len(tracks_with_segments)} total, mostrando primeros 15):")
        for t in tracks_with_segments[:15]:
            print(f"  Track {t['track_id']}: {t['movement']}")
            print(f"    {t['crossings']} cruces en {t['unique_accesses']} accesos diferentes")
            print(f"    {t['changes']} cambios de acceso -> deberia generar {t['expected_segments']} segmentos")
    else:
        print(f"\n>> ⚠️ NO se encontraron tracks con cambios de acceso!")
        print(f"   Esto significa que ningún vehículo sale de un acceso y vuelve a entrar por otro.")

if __name__ == '__main__':
    # Analizar un track específico
    # Usar el primer track del playback
    data_dir = Path('data') / 'dataset_f8144347'
    playback_file = data_dir / 'playback_events.json'
    playback = json.load(open(playback_file, encoding='utf-8'))
    first_track_id = playback['events'][0]['track_id'] if playback['events'] else None

    if first_track_id:
        debug_track(track_id=first_track_id)

    print("\n" + "="*80 + "\n")

    # Analizar todos los tracks
    analyze_all_tracks()
