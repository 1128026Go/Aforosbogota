"""
Script para detectar trayectorias fragmentadas (mismo vehiculo con multiples IDs)

Detecta casos donde:
1. Dos trayectorias tienen clase similar
2. La segunda empieza cerca de donde termino la primera (espacial y temporal)
3. La direccion de movimiento es consistente

Genera un reporte para revisar y posiblemente fusionar.
"""
import json
import pickle
import math
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def euclidean_distance(p1, p2):
    """Distancia euclidiana entre dos puntos"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def get_direction(positions):
    """Calcula direccion general de movimiento (angulo en grados)"""
    if len(positions) < 2:
        return None

    start = positions[0]
    end = positions[-1]

    dx = end[0] - start[0]
    dy = end[1] - start[1]

    # Angulo en grados (0 = este, 90 = norte, 180 = oeste, 270 = sur)
    angle = math.degrees(math.atan2(-dy, dx))  # -dy porque Y crece hacia abajo
    return angle % 360

def angle_difference(a1, a2):
    """Diferencia minima entre dos angulos (0-180 grados)"""
    if a1 is None or a2 is None:
        return 180
    diff = abs(a1 - a2)
    if diff > 180:
        diff = 360 - diff
    return diff

def detect_fragmented_trajectories(dataset_id='dataset_f8144347'):
    """Detecta trayectorias que probablemente son fragmentos del mismo vehiculo"""

    data_dir = Path('data') / dataset_id
    playback_file = data_dir / 'playback_events.json'

    print(">> Cargando playback...")
    with open(playback_file, encoding='utf-8') as f:
        playback = json.load(f)

    events = playback['events']
    print(f"   Total eventos: {len(events)}")

    # Ordenar por frame de salida
    events_sorted = sorted(events, key=lambda e: e.get('frame_exit', e.get('frame_entry', 0)))

    # Parametros de deteccion
    MAX_TIME_GAP = 30  # frames (1 segundo a 30fps)
    MAX_SPATIAL_GAP = 150  # pixels
    MAX_ANGLE_DIFF = 45  # grados

    print("\n>> Buscando fragmentaciones...")
    print(f"   Parametros:")
    print(f"     - Gap temporal maximo: {MAX_TIME_GAP} frames")
    print(f"     - Gap espacial maximo: {MAX_SPATIAL_GAP} pixels")
    print(f"     - Diferencia angular maxima: {MAX_ANGLE_DIFF} grados")

    candidates = []

    for i, e1 in enumerate(events_sorted):
        # Solo revisar los proximos N eventos (ventana temporal)
        for e2 in events_sorted[i+1:i+50]:
            # Mismo track? Skip
            if e1['track_id'] == e2['track_id']:
                continue

            # Misma clase o clases similares (car/motorcycle confundibles)
            compatible_classes = (
                e1['class'] == e2['class'] or
                (e1['class'] in ['car', 'motorcycle'] and e2['class'] in ['car', 'motorcycle'])
            )
            if not compatible_classes:
                continue

            # Temporal: e2 empieza poco despues de que e1 termina
            t1_end = e1.get('frame_exit', e1.get('frame_entry', 0))
            t2_start = e2.get('frame_entry', 0)
            time_gap = t2_start - t1_end

            if time_gap < 0 or time_gap > MAX_TIME_GAP:
                continue

            # Espacial: e2 empieza cerca de donde e1 termina
            pos1_end = e1['positions'][-1]
            pos2_start = e2['positions'][0]
            spatial_gap = euclidean_distance(pos1_end, pos2_start)

            if spatial_gap > MAX_SPATIAL_GAP:
                continue

            # Direccion: angulos similares
            dir1 = get_direction(e1['positions'])
            dir2 = get_direction(e2['positions'])
            angle_diff = angle_difference(dir1, dir2)

            if angle_diff > MAX_ANGLE_DIFF:
                continue

            # Posible fragmentacion detectada!
            candidates.append({
                'track1_id': str(e1['track_id']),
                'track2_id': str(e2['track_id']),
                'class1': e1['class'],
                'class2': e2['class'],
                'time_gap': time_gap,
                'spatial_gap': round(spatial_gap, 1),
                'angle_diff': round(angle_diff, 1),
                'origin1': e1.get('origin'),
                'dest1': e1.get('destination'),
                'origin2': e2.get('origin'),
                'dest2': e2.get('destination'),
                'confidence': 'high' if (time_gap < 10 and spatial_gap < 50 and angle_diff < 20) else 'medium'
            })

    print(f"\n>> RESULTADO:")
    print(f"   Fragmentaciones detectadas: {len(candidates)}")

    # Agrupar por confianza
    by_conf = defaultdict(list)
    for c in candidates:
        by_conf[c['confidence']].append(c)

    for conf in ['high', 'medium']:
        if conf in by_conf:
            print(f"     {conf}: {len(by_conf[conf])}")

    # Mostrar ejemplos
    print(f"\n>> Ejemplos (primeros 15):")
    for i, c in enumerate(candidates[:15]):
        print(f"\n  [{i+1}] Tracks {c['track1_id']} + {c['track2_id']} (confianza: {c['confidence']})")
        print(f"      Clase: {c['class1']} -> {c['class2']}")
        print(f"      Movimiento: {c['origin1']}->{c['dest1']} + {c['origin2']}->{c['dest2']}")
        print(f"      Gap temporal: {c['time_gap']} frames")
        print(f"      Gap espacial: {c['spatial_gap']} px")
        print(f"      Diferencia angular: {c['angle_diff']} grados")

    if len(candidates) > 15:
        print(f"\n  ... y {len(candidates) - 15} mas")

    # Guardar reporte
    report_file = data_dir / 'fragmentation_report.json'
    report = {
        'analysis_date': datetime.now().isoformat(),
        'parameters': {
            'max_time_gap': MAX_TIME_GAP,
            'max_spatial_gap': MAX_SPATIAL_GAP,
            'max_angle_diff': MAX_ANGLE_DIFF
        },
        'summary': {
            'total_events': len(events),
            'fragmentations_detected': len(candidates),
            'high_confidence': len(by_conf['high']),
            'medium_confidence': len(by_conf['medium'])
        },
        'candidates': candidates
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n>> Reporte guardado en: {report_file}")
    print("\n>> IMPORTANTE:")
    print("   Este es solo un analisis. Revisa los casos en el visualizador.")
    print("   Para casos claros, puedes descartar uno de los dos tracks.")
    print("   En el futuro se podria implementar fusion automatica.")

    return report

if __name__ == '__main__':
    report = detect_fragmented_trajectories()
