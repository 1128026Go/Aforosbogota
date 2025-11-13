"""
Script de Diagnóstico de Tracks
================================

Analiza un archivo de tracks y muestra estadísticas detalladas
sobre las clases detectadas por YOLO.

Uso:
    python diagnostico_tracks.py tracks.json
    python diagnostico_tracks.py tracks.pkl

Autor: Sistema RILSA
Fecha: 2025-11-09
"""

import json
import sys
import pickle
from pathlib import Path
from collections import Counter


def cargar_tracks(archivo: str):
    """Carga tracks desde JSON o PKL"""
    extension = Path(archivo).suffix.lower()

    if extension == '.json':
        with open(archivo, 'r') as f:
            data = json.load(f)
    elif extension in ['.pkl', '.pickle']:
        with open(archivo, 'rb') as f:
            data = pickle.load(f)
    else:
        raise ValueError(f"Formato no soportado: {extension}")

    # Extraer tracks
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'tracks' in data:
        return data['tracks']
    else:
        raise ValueError("Formato de archivo no reconocido")


def analizar_tracks(tracks):
    """Analiza tracks y genera estadísticas"""
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO DE TRACKS")
    print("=" * 80)

    total_tracks = len(tracks)
    print(f"\nTotal de tracks: {total_tracks}")

    # Contar clases
    clases = []
    tracks_con_clase = 0
    tracks_sin_clase = 0

    for track in tracks:
        # Intentar obtener clase de diferentes campos
        clase = track.get('class') or track.get('cls') or track.get('label')

        if clase:
            clases.append(str(clase).lower().strip())
            tracks_con_clase += 1
        else:
            tracks_sin_clase += 1

    print(f"Tracks con clase: {tracks_con_clase}")
    print(f"Tracks sin clase: {tracks_sin_clase}")

    # Estadísticas por clase
    if clases:
        contador_clases = Counter(clases)

        print("\n" + "-" * 80)
        print("DISTRIBUCIÓN POR CLASE")
        print("-" * 80)

        # Definir clases vehiculares y peatonales
        vehiculares = {
            'car', 'auto', 'automovil', 'carro',
            'motorcycle', 'moto', 'motocicleta',
            'bus', 'autobus', 'buseta',
            'truck', 'camion',
            'bicycle', 'bike', 'bicicleta',
            'taxi', 'van', 'camioneta'
        }

        peatonales = {'person', 'peaton', 'pedestrian', 'peatones'}

        total_vehiculares = 0
        total_peatonales = 0
        total_otros = 0

        print("\n📊 RESUMEN:")
        print(f"{'Clase':<20} {'Cantidad':<12} {'Porcentaje':<12} {'Tipo'}")
        print("-" * 80)

        for clase, cantidad in contador_clases.most_common():
            porcentaje = (cantidad / tracks_con_clase) * 100

            # Clasificar
            if clase in vehiculares:
                tipo = "🚗 VEHICULAR"
                total_vehiculares += cantidad
            elif clase in peatonales:
                tipo = "🚶 PEATONAL"
                total_peatonales += cantidad
            else:
                tipo = "❓ OTRO"
                total_otros += cantidad

            print(f"{clase:<20} {cantidad:<12} {porcentaje:>6.2f}%      {tipo}")

        print("-" * 80)
        print(f"{'TOTAL VEHICULARES':<20} {total_vehiculares:<12} {(total_vehiculares/tracks_con_clase)*100:>6.2f}%")
        print(f"{'TOTAL PEATONALES':<20} {total_peatonales:<12} {(total_peatonales/tracks_con_clase)*100:>6.2f}%")
        if total_otros > 0:
            print(f"{'TOTAL OTROS':<20} {total_otros:<12} {(total_otros/tracks_con_clase)*100:>6.2f}%")

        # Verificar tracks específicos de peatones si el usuario pregunta
        if total_peatonales > 0:
            print("\n" + "-" * 80)
            print("MUESTRA DE PEATONES DETECTADOS (primeros 10 track_ids)")
            print("-" * 80)

            peatones_mostrados = 0
            for track in tracks:
                clase = (track.get('class') or track.get('cls') or track.get('label') or '').lower().strip()

                if clase in peatonales and peatones_mostrados < 10:
                    track_id = track.get('track_id', '?')
                    first_frame = track.get('first_frame', track.get('frame', '?'))
                    last_frame = track.get('last_frame', '?')
                    duracion = '?' if first_frame == '?' or last_frame == '?' else last_frame - first_frame

                    print(f"  Track ID: {track_id:<8} | Clase: {clase:<12} | Frames: {first_frame}-{last_frame} (duración: {duracion})")
                    peatones_mostrados += 1

                if peatones_mostrados >= 10:
                    break

            if total_peatonales > 10:
                print(f"  ... y {total_peatonales - 10} peatones más")

    # Verificar campos de trayectoria
    print("\n" + "-" * 80)
    print("VERIFICACIÓN DE CAMPOS")
    print("-" * 80)

    campos_comunes = ['track_id', 'class', 'cls', 'trajectory', 'first_frame', 'last_frame']
    for campo in campos_comunes:
        tracks_con_campo = sum(1 for t in tracks if campo in t)
        porcentaje = (tracks_con_campo / total_tracks) * 100
        print(f"  {campo:<20}: {tracks_con_campo}/{total_tracks} ({porcentaje:.1f}%)")

    print("\n" + "=" * 80)

    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")

    if tracks_sin_clase > 0:
        print(f"  ⚠ {tracks_sin_clase} tracks sin clase - verifica el formato de entrada")

    if total_peatonales == 0:
        print("  ⚠ No se detectaron peatones - verifica que:")
        print("     - El video incluya peatones")
        print("     - YOLO esté configurado para detectar 'person'")
        print("     - Los tracks no estén pre-filtrados")
    elif total_peatonales < 10:
        print(f"  ⚠ Solo {total_peatonales} peatones detectados - puede ser normal si hay poco flujo peatonal")
    else:
        print(f"  ✓ {total_peatonales} peatones detectados - se procesarán correctamente")

    if total_vehiculares == 0:
        print("  ⚠ No se detectaron vehículos - verifica el archivo de entrada")
    else:
        print(f"  ✓ {total_vehiculares} vehículos detectados")

    print("\n" + "=" * 80)


def main():
    if len(sys.argv) < 2:
        print("Uso: python diagnostico_tracks.py <archivo_tracks.json|pkl>")
        return 1

    archivo = sys.argv[1]

    if not Path(archivo).exists():
        print(f"❌ Archivo no encontrado: {archivo}")
        return 1

    try:
        print(f"\n📁 Analizando: {archivo}")
        tracks = cargar_tracks(archivo)
        analizar_tracks(tracks)
        return 0

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
