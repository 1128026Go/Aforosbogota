"""
Script para analizar y reclasificar automáticamente trayectorias
basándose en el tamaño del bounding box y otras características.

Este script NO modifica nada, solo genera un reporte y un archivo
de correcciones sugeridas que puedes revisar antes de aplicar.
"""
import json
import pickle
from pathlib import Path
from collections import Counter, defaultdict
import statistics

def analyze_bbox_sizes(dataset_id='dataset_f8144347'):
    """Analiza el tamaño de bbox de cada clase para establecer umbrales"""

    data_dir = Path('data') / dataset_id
    pkl_file = data_dir / 'raw.pkl'
    playback_file = data_dir / 'playback_events.json'

    # Cargar datos
    print(">> Cargando datos...")
    raw_data = pickle.load(open(pkl_file, 'rb'))
    playback = json.load(open(playback_file))

    detecciones = raw_data['detecciones']

    # Crear mapeo de frame + bbox -> clase
    # Para cada detección, calcular área
    frame_class_areas = defaultdict(lambda: defaultdict(list))

    for det in detecciones:
        frame = det['fotograma']
        clase = det['clase']
        bbox = det['bbox']  # [x1, y1, x2, y2]

        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        area = width * height

        frame_class_areas[clase]['areas'].append(area)
        frame_class_areas[clase]['widths'].append(width)
        frame_class_areas[clase]['heights'].append(height)

    # Calcular estadísticas por clase
    print("\n>> ESTADISTICAS DE TAMANO POR CLASE (en detecciones YOLO):")
    print("=" * 80)

    class_stats = {}
    for clase in ['car', 'motorcycle', 'person', 'truck', 'bus', 'bicycle']:
        if clase not in frame_class_areas:
            continue

        areas = frame_class_areas[clase]['areas']
        if not areas:
            continue

        stats = {
            'count': len(areas),
            'mean_area': statistics.mean(areas),
            'median_area': statistics.median(areas),
            'min_area': min(areas),
            'max_area': max(areas),
            'p25': statistics.quantiles(areas, n=4)[0],
            'p75': statistics.quantiles(areas, n=4)[2],
        }
        class_stats[clase] = stats

        print(f"\n{clase.upper()}:")
        print(f"  Cantidad: {stats['count']:,}")
        print(f"  Área promedio: {stats['mean_area']:.0f} px²")
        print(f"  Área mediana: {stats['median_area']:.0f} px²")
        print(f"  Rango: {stats['min_area']:.0f} - {stats['max_area']:.0f} px²")
        print(f"  Cuartiles (25%-75%): {stats['p25']:.0f} - {stats['p75']:.0f} px²")

    # Ahora analizar las trayectorias del playback
    print("\n\n>> ANALISIS DE TRAYECTORIAS EN PLAYBACK:")
    print("=" * 80)

    # Para cada track, calcular área promedio de su bbox
    track_analysis = []

    for event in playback['events']:
        track_id = event['track_id']
        clase = event['class']
        positions = event['positions']

        # El problema es que positions solo tiene [x,y] no bbox
        # Necesitamos obtener bbox de las detecciones originales
        # Vamos a estimar área basándonos en el spread de posiciones

        if len(positions) < 5:  # Muy corto para analizar
            continue

        # Calcular spread de posiciones (aproximación burda del tamaño)
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]

        width_approx = max(xs) - min(xs)
        height_approx = max(ys) - min(ys)

        # Esto NO es el bbox real, pero nos da una idea del espacio ocupado
        spread_area = width_approx * height_approx

        track_analysis.append({
            'track_id': track_id,
            'class': clase,
            'spread_area': spread_area,
            'positions_count': len(positions),
            'frame_entry': event.get('frame_entry'),
            'frame_exit': event.get('frame_exit'),
        })

    # Agrupar por clase
    class_tracks = defaultdict(list)
    for track in track_analysis:
        class_tracks[track['class']].append(track['spread_area'])

    print("\nDistribución de 'spread area' por clase en tracks:")
    for clase in ['car', 'motorcycle', 'person']:
        if clase not in class_tracks or not class_tracks[clase]:
            continue
        areas = class_tracks[clase]
        print(f"\n{clase.upper()} ({len(areas)} tracks):")
        print(f"  Spread promedio: {statistics.mean(areas):.0f}")
        print(f"  Spread mediano: {statistics.median(areas):.0f}")
        if len(areas) > 3:
            print(f"  Cuartiles: {statistics.quantiles(areas, n=4)[0]:.0f} - {statistics.quantiles(areas, n=4)[2]:.0f}")

    # Generar sugerencias de reclasificación
    print("\n\n>> SUGERENCIAS DE RECLASIFICACION:")
    print("=" * 80)

    # Definir umbrales basados en las estadísticas
    # CONSERVADOR CON PEATONES: Más motos que personas
    THRESHOLDS = {
        'motorcycle_max_spread': 60000,  # Más permisivo para capturar motos
        'person_max_spread': 5000,       # Conservador - solo peatones muy claros (mediana real = 1,181)
    }

    suggested_corrections = []

    cars_classified = [t for t in track_analysis if t['class'] == 'car']

    to_motorcycle = 0
    to_person = 0

    for track in cars_classified:
        spread = track['spread_area']
        suggestion = None

        if spread < THRESHOLDS['person_max_spread']:
            suggestion = 'person'
            to_person += 1
        elif spread < THRESHOLDS['motorcycle_max_spread']:
            suggestion = 'motorcycle'
            to_motorcycle += 1

        if suggestion:
            suggested_corrections.append({
                'track_id': str(track['track_id']),
                'original_class': 'car',
                'suggested_class': suggestion,
                'spread_area': spread,
                'confidence': 'medium' if spread < THRESHOLDS['motorcycle_max_spread'] * 0.8 else 'low'
            })

    print(f"\n>> Resumen de sugerencias:")
    print(f"  Total 'car' analizados: {len(cars_classified)}")
    print(f"  Sugeridos para cambiar a 'motorcycle': {to_motorcycle}")
    print(f"  Sugeridos para cambiar a 'person': {to_person}")
    print(f"  Total correcciones sugeridas: {len(suggested_corrections)}")

    # Mostrar algunos ejemplos
    print(f"\n>> Ejemplos de correcciones sugeridas:")
    for i, corr in enumerate(suggested_corrections[:10]):
        print(f"  Track {corr['track_id']}: car -> {corr['suggested_class']} (spread={corr['spread_area']:.0f}, conf={corr['confidence']})")

    if len(suggested_corrections) > 10:
        print(f"  ... y {len(suggested_corrections) - 10} más")

    # Guardar reporte
    report_file = data_dir / 'reclassification_suggestions.json'
    report = {
        'analysis_date': '2025-11-10',
        'thresholds': THRESHOLDS,
        'class_statistics': class_stats,
        'summary': {
            'total_cars': len(cars_classified),
            'suggested_to_motorcycle': to_motorcycle,
            'suggested_to_person': to_person,
        },
        'suggestions': suggested_corrections
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n>> Reporte guardado en: {report_file}")
    print("\n>> IMPORTANTE: Este es solo un analisis. Revisa los resultados antes de aplicar.")
    print("   El metodo de 'spread area' es una aproximacion burda.")
    print("   Para mayor precision, necesitamos acceder a los bbox originales por frame.")

    return report

if __name__ == '__main__':
    report = analyze_bbox_sizes()
