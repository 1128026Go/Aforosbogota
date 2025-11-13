"""
Test de Asignación RILSA - Acceso Oeste
========================================

Crea tracks de prueba desde Oeste y verifica qué código se asigna.
"""

import sys
import json
import importlib
from pathlib import Path

# Agregar path de módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'modules'))

# Forzar recarga del módulo
import rilsa_assignment
importlib.reload(rilsa_assignment)
from rilsa_assignment import AsignadorRILSA, crear_configuracion_simple

def crear_track_prueba(track_id, origen_x, origen_y, destino_x, destino_y, clase='car'):
    """Crea un track de prueba"""
    # Generar trayectoria interpolada
    n_puntos = 20
    trayectoria = []

    for i in range(n_puntos):
        t = i / (n_puntos - 1)
        x = origen_x + (destino_x - origen_x) * t
        y = origen_y + (destino_y - origen_y) * t
        trayectoria.append({'x': x, 'y': y})

    return {
        'track_id': track_id,
        'class': clase,
        'trajectory': trayectoria
    }

def main():
    print("=" * 80)
    print("TEST DE ASIGNACIÓN RILSA - ACCESO OESTE")
    print("=" * 80)

    # Crear configuración (centro en 500, 500)
    config = crear_configuracion_simple(500, 500, tamano=200)
    asignador = AsignadorRILSA(config)

    print(f"\nCentro de intersección: ({config.centro[0]}, {config.centro[1]})")
    print(f"Radio interior: {config.radio_interior}")

    # Crear tracks de prueba desde Oeste
    print("\n" + "=" * 80)
    print("CREANDO TRACKS DE PRUEBA DESDE OESTE")
    print("=" * 80)

    # Coordenadas de prueba (asumiendo centro en 500, 500)
    # Oeste está a la izquierda (x < 500)
    # Norte arriba (y < 500)
    # Sur abajo (y > 500)
    # Este derecha (x > 500)

    tracks_prueba = [
        {
            'nombre': 'Oeste → Este (Directo)',
            'track': crear_track_prueba(1, 200, 500, 800, 500),  # Horizontal izq→der
            'esperado': '3'
        },
        {
            'nombre': 'Oeste → Sur (Izquierda)',
            'track': crear_track_prueba(2, 200, 500, 500, 800),  # Izq→Abajo
            'esperado': '7'
        },
        {
            'nombre': 'Oeste → Norte (Derecha)',
            'track': crear_track_prueba(3, 200, 500, 500, 200),  # Izq→Arriba
            'esperado': '9(3)'
        }
    ]

    # Procesar cada track
    todo_correcto = True

    for test in tracks_prueba:
        print(f"\n{'=' * 80}")
        print(f"TEST: {test['nombre']}")
        print(f"{'=' * 80}")

        track = test['track']
        esperado = test['esperado']

        # Mostrar trayectoria
        traj = track['trajectory']
        print(f"\nTrayectoria:")
        print(f"  Inicio: ({traj[0]['x']:.1f}, {traj[0]['y']:.1f})")
        print(f"  Fin:    ({traj[-1]['x']:.1f}, {traj[-1]['y']:.1f})")

        # Asignar código
        codigo, origen, destino = asignador.asignar_codigo_rilsa(track)

        print(f"\nResultado de asignación:")
        print(f"  Origen detectado:  {origen}")
        print(f"  Destino detectado: {destino}")
        print(f"  Código asignado:   {codigo}")
        print(f"  Código esperado:   {esperado}")

        # Verificar
        if codigo == esperado:
            print(f"\n  ✅ CORRECTO")
        else:
            print(f"\n  ❌ ERROR: Esperaba '{esperado}' pero obtuvo '{codigo}'")
            todo_correcto = False

            # Diagnóstico adicional
            print(f"\n  Diagnóstico:")
            print(f"    - Mapeo ({origen}, {destino}) → {asignador.mapeo_rilsa.get((origen, destino), 'NO ENCONTRADO')}")

    # Resumen final
    print(f"\n{'=' * 80}")
    print("RESUMEN")
    print(f"{'=' * 80}")

    if todo_correcto:
        print("\n✅ TODOS LOS TESTS PASARON")
        print("\nEl mapeo RILSA está correcto y la asignación funciona bien.")
        print("\nSi aún ves códigos incorrectos en tus CSVs, verifica:")
        print("  1. ¿Qué archivo de zonas estás usando? (--zonas)")
        print("  2. ¿Las zonas están bien definidas?")
        print("  3. ¿Estás viendo el CSV correcto (el recién generado)?")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        print("\nPosibles causas:")
        print("  1. El código no se recargó correctamente")
        print("  2. Hay un problema en determinar_acceso()")
        print("  3. El mapeo no se actualizó")

    print(f"\n{'=' * 80}\n")

    return 0 if todo_correcto else 1


if __name__ == "__main__":
    sys.exit(main())
