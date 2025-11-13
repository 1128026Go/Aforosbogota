"""
Script de Análisis de Detecciones en PKL
=========================================

Analiza un archivo PKL de detecciones YOLO y muestra estadísticas
detalladas sobre peatones y vehículos detectados FRAME POR FRAME.

Este script te permite ver cuántos peatones detectó YOLO originalmente,
antes de cualquier filtrado en el pipeline.

Uso:
    python analizar_pkl_peatones.py archivo.pkl
    python analizar_pkl_peatones.py archivo.pkl --frames 100

Autor: Sistema RILSA
Fecha: 2025-11-09
"""

import pickle
import sys
from pathlib import Path
from collections import Counter, defaultdict
import argparse


def analizar_pkl(archivo_pkl: str, max_frames: int = None):
    """Analiza detecciones en un PKL frame por frame"""

    print("\n" + "=" * 80)
    print("ANÁLISIS DE DETECCIONES YOLO EN PKL")
    print("=" * 80)
    print(f"\n📁 Archivo: {archivo_pkl}\n")

    # Cargar PKL
    print("Cargando archivo PKL...")
    with open(archivo_pkl, 'rb') as f:
        data = pickle.load(f)

    print(f"✓ PKL cargado\n")

    # Analizar estructura
    print("-" * 80)
    print("ESTRUCTURA DEL PKL")
    print("-" * 80)

    if isinstance(data, dict):
        print(f"Tipo: Diccionario con {len(data)} claves")
        print(f"Claves disponibles: {list(data.keys())}")

        # Intentar encontrar las detecciones
        if 'detections' in data:
            detections = data['detections']
            print(f"\n✓ Encontradas 'detections': {len(detections)} frames")
        elif 'results' in data:
            detections = data['results']
            print(f"\n✓ Encontradas 'results': {len(detections)} frames")
        elif 'frames' in data:
            detections = data['frames']
            print(f"\n✓ Encontradas 'frames': {len(detections)} frames")
        else:
            # Asumir que el primer valor de tipo lista es las detecciones
            for key, value in data.items():
                if isinstance(value, (list, dict)) and len(value) > 0:
                    detections = value
                    print(f"\n✓ Asumiendo '{key}' como detecciones: {len(detections)} frames")
                    break
            else:
                print("\n❌ No se encontró lista de detecciones en el PKL")
                return

    elif isinstance(data, list):
        detections = data
        print(f"Tipo: Lista directa con {len(detections)} frames")

    else:
        print(f"❌ Tipo no reconocido: {type(data)}")
        return

    # Limitar frames si se especificó
    if max_frames:
        detections = detections[:max_frames]
        print(f"\n⚠ Análisis limitado a primeros {max_frames} frames")

    # Analizar detecciones frame por frame
    print("\n" + "-" * 80)
    print("ANÁLISIS FRAME POR FRAME")
    print("-" * 80)

    total_frames = len(detections)
    frames_con_detecciones = 0
    frames_vacios = 0

    # Contadores globales
    contador_clases = Counter()
    detecciones_por_frame = []
    peatones_por_frame = []
    vehiculos_por_frame = []

    # Clases vehiculares
    clases_vehiculares = {
        'car', 'auto', 'automovil', 'carro',
        'motorcycle', 'moto', 'motocicleta',
        'bus', 'autobus', 'buseta',
        'truck', 'camion',
        'bicycle', 'bike', 'bicicleta',
        'taxi', 'van', 'camioneta'
    }

    clases_peatonales = {'person', 'peaton', 'pedestrian', 'peatones'}

    print(f"\nAnalizando {total_frames} frames...\n")

    for frame_idx, frame_data in enumerate(detections):
        # Extraer detecciones del frame
        if isinstance(frame_data, dict):
            # Puede estar en diferentes campos
            if 'boxes' in frame_data:
                boxes = frame_data['boxes']
            elif 'detections' in frame_data:
                boxes = frame_data['detections']
            elif 'objects' in frame_data:
                boxes = frame_data['objects']
            else:
                # Asumir que el dict ES una detección
                boxes = [frame_data]
        elif isinstance(frame_data, list):
            boxes = frame_data
        else:
            boxes = []

        if not boxes or len(boxes) == 0:
            frames_vacios += 1
            detecciones_por_frame.append(0)
            peatones_por_frame.append(0)
            vehiculos_por_frame.append(0)
            continue

        frames_con_detecciones += 1

        # Contar clases en este frame
        peatones_frame = 0
        vehiculos_frame = 0

        for box in boxes:
            # Extraer clase
            if isinstance(box, dict):
                clase = box.get('class', box.get('cls', box.get('label', box.get('name', 'unknown'))))
            else:
                # Puede ser una tupla o lista
                clase = 'unknown'

            clase_str = str(clase).lower().strip()
            contador_clases[clase_str] += 1

            if clase_str in clases_peatonales:
                peatones_frame += 1
            elif clase_str in clases_vehiculares:
                vehiculos_frame += 1

        detecciones_por_frame.append(len(boxes))
        peatones_por_frame.append(peatones_frame)
        vehiculos_por_frame.append(vehiculos_frame)

    # Estadísticas generales
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS GENERALES")
    print("=" * 80)

    print(f"\nTotal de frames analizados: {total_frames}")
    print(f"Frames con detecciones: {frames_con_detecciones} ({frames_con_detecciones/total_frames*100:.1f}%)")
    print(f"Frames vacíos: {frames_vacios} ({frames_vacios/total_frames*100:.1f}%)")

    total_detecciones = sum(detecciones_por_frame)
    print(f"\nTotal de detecciones: {total_detecciones}")
    print(f"Promedio por frame: {total_detecciones/total_frames:.1f}")

    # Distribución por clase
    print("\n" + "-" * 80)
    print("DISTRIBUCIÓN POR CLASE")
    print("-" * 80)

    total_peatones = sum(peatones_por_frame)
    total_vehiculos = sum(vehiculos_por_frame)
    total_otros = total_detecciones - total_peatones - total_vehiculos

    print(f"\n{'Categoría':<20} {'Total':<12} {'Promedio/Frame':<18} {'Porcentaje'}")
    print("-" * 80)
    print(f"{'PEATONES':<20} {total_peatones:<12} {total_peatones/total_frames:<18.2f} {total_peatones/total_detecciones*100:>6.1f}%")
    print(f"{'VEHÍCULOS':<20} {total_vehiculos:<12} {total_vehiculos/total_frames:<18.2f} {total_vehiculos/total_detecciones*100:>6.1f}%")
    if total_otros > 0:
        print(f"{'OTROS':<20} {total_otros:<12} {total_otros/total_frames:<18.2f} {total_otros/total_detecciones*100:>6.1f}%")

    # Detalle por clase
    print("\n" + "-" * 80)
    print("DETALLE POR CLASE ESPECÍFICA")
    print("-" * 80)

    print(f"\n{'Clase':<20} {'Total':<12} {'Promedio/Frame':<18} {'Tipo'}")
    print("-" * 80)

    for clase, cantidad in contador_clases.most_common():
        promedio = cantidad / total_frames

        if clase in clases_peatonales:
            tipo = "🚶 PEATÓN"
        elif clase in clases_vehiculares:
            tipo = "🚗 VEHÍCULO"
        else:
            tipo = "❓ OTRO"

        print(f"{clase:<20} {cantidad:<12} {promedio:<18.2f} {tipo}")

    # Estadísticas de peatones
    if total_peatones > 0:
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS DE PEATONES")
        print("=" * 80)

        frames_con_peatones = sum(1 for p in peatones_por_frame if p > 0)
        max_peatones_frame = max(peatones_por_frame)

        print(f"\nTotal de peatones detectados: {total_peatones}")
        print(f"Frames con peatones: {frames_con_peatones} ({frames_con_peatones/total_frames*100:.1f}%)")
        print(f"Promedio de peatones por frame: {total_peatones/total_frames:.2f}")
        print(f"Máximo de peatones en un frame: {max_peatones_frame}")

        # Mostrar algunos frames con muchos peatones
        print("\n" + "-" * 80)
        print("FRAMES CON MÁS PEATONES (top 10)")
        print("-" * 80)

        frames_ordenados = sorted(enumerate(peatones_por_frame), key=lambda x: x[1], reverse=True)[:10]

        print(f"\n{'Frame':<10} {'Peatones':<12} {'Total Detecciones'}")
        print("-" * 80)
        for frame_idx, num_peatones in frames_ordenados:
            if num_peatones > 0:
                print(f"{frame_idx:<10} {num_peatones:<12} {detecciones_por_frame[frame_idx]}")

    else:
        print("\n⚠ NO SE DETECTARON PEATONES EN NINGÚN FRAME")
        print("   Posibles causas:")
        print("   - El video no incluye peatones")
        print("   - YOLO no está configurado para detectar 'person'")
        print("   - El modelo de YOLO usado no detecta personas")

    print("\n" + "=" * 80)

    # Recomendaciones
    print("\n💡 INTERPRETACIÓN:")

    if total_peatones == 0:
        print("  ❌ No hay peatones en el PKL - el problema está en la detección YOLO")
    elif total_peatones < 100:
        print(f"  ⚠ Hay {total_peatones} peatones en el PKL - puede ser normal si hay poco flujo peatonal")
    else:
        print(f"  ✓ Hay {total_peatones} peatones en el PKL - YOLO los detectó correctamente")
        print(f"    Si ves menos en el aforo final, el problema está en el pipeline de procesamiento")

    print("\n" + "=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Analiza detecciones YOLO en un archivo PKL',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('pkl_file', help='Archivo PKL a analizar')
    parser.add_argument('--frames', type=int, help='Limitar análisis a N primeros frames')

    args = parser.parse_args()

    if not Path(args.pkl_file).exists():
        print(f"❌ Archivo no encontrado: {args.pkl_file}")
        return 1

    try:
        analizar_pkl(args.pkl_file, args.frames)
        return 0

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
