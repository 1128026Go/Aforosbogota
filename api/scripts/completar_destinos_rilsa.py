"""
Script para completar destination_cardinal basándose en origin_cardinal + mov_rilsa

Usa el mapeo estándar RILSA para inferir el destino cuando:
- El evento tiene origin_cardinal
- El evento tiene mov_rilsa
- El evento no tiene dest_cardinal o está incorrecto

Mapeo RILSA:
- Directos (1-4): N→S, S→N, O→E, E→O
- Izquierdas (5-8): N→E, S→O, O→N, E→S
- Derechas (91-94): N→O, S→E, O→S, E→N
- U-turns (101-104): N→N, S→S, O→O, E→E
"""

import json
from pathlib import Path
from typing import Dict, Optional
import sys

# Mapeo RILSA: (origen, mov_rilsa) -> destino
MAPEO_RILSA_DESTINO = {
    # Directos (1-4)
    ('N', 1): 'S',   # Norte → Sur
    ('S', 2): 'N',   # Sur → Norte
    ('O', 3): 'E',   # Oeste → Este
    ('E', 4): 'O',   # Este → Oeste

    # Izquierdas (5-8)
    ('N', 5): 'E',   # Norte → Este
    ('S', 6): 'O',   # Sur → Oeste
    ('O', 7): 'N',   # Oeste → Norte
    ('E', 8): 'S',   # Este → Sur

    # Derechas (91-94)
    ('N', 91): 'O',  # Norte → Oeste
    ('S', 92): 'E',  # Sur → Este
    ('O', 93): 'S',  # Oeste → Sur
    ('E', 94): 'N',  # Este → Norte

    # U-turns (101-104)
    ('N', 101): 'N', # Giro en U en Norte
    ('S', 102): 'S', # Giro en U en Sur
    ('O', 103): 'O', # Giro en U en Oeste
    ('E', 104): 'E', # Giro en U en Este
}


def obtener_destino_por_rilsa(origen: str, mov_rilsa: int) -> Optional[str]:
    """
    Obtiene el destino cardinal basándose en origen y movimiento RILSA.

    Args:
        origen: Punto cardinal de origen (N, S, E, O)
        mov_rilsa: Código de movimiento RILSA

    Returns:
        Punto cardinal de destino o None si no se encuentra
    """
    return MAPEO_RILSA_DESTINO.get((origen, mov_rilsa))


def completar_destinos(dataset_id: str, base_path: str = "data") -> Dict:
    """
    Completa los destination_cardinal faltantes en un dataset.

    Args:
        dataset_id: ID del dataset (ej: "dataset_f8144347")
        base_path: Ruta base de datos (por defecto "data")

    Returns:
        Dict con estadísticas de la operación
    """
    # Construir rutas
    script_dir = Path(__file__).parent.parent  # Sube a api/
    data_path = script_dir / base_path / dataset_id
    playback_file = data_path / "playback_events.json"

    if not playback_file.exists():
        return {
            "error": f"No se encontró el archivo {playback_file}",
            "success": False
        }

    print(f"📂 Procesando: {playback_file}")

    # Leer eventos
    with open(playback_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    eventos = data.get("events", [])
    total = len(eventos)

    # Estadísticas
    stats = {
        "total_eventos": total,
        "con_destino_original": 0,
        "sin_destino": 0,
        "destino_corregido": 0,
        "destino_agregado": 0,
        "sin_info_suficiente": 0,
        "movimientos_sin_mapeo": set(),
        "success": True
    }

    # Procesar cada evento
    for evento in eventos:
        origen = evento.get("origin_cardinal")
        mov_rilsa = evento.get("mov_rilsa")
        dest_actual = evento.get("dest_cardinal") or evento.get("destination_cardinal")

        # Si tiene destino válido, contar y continuar
        if dest_actual and dest_actual in ['N', 'S', 'E', 'O']:
            stats["con_destino_original"] += 1
            continue

        # Si no tiene origen o mov_rilsa, no se puede inferir
        if not origen or mov_rilsa is None:
            stats["sin_info_suficiente"] += 1
            continue

        # Buscar destino en el mapeo RILSA
        destino_inferido = obtener_destino_por_rilsa(origen, mov_rilsa)

        if destino_inferido:
            # Verificar si es corrección o adición
            if dest_actual and dest_actual != destino_inferido:
                stats["destino_corregido"] += 1
                print(f"  ✏️  Track {evento.get('track_id')}: {origen}→{dest_actual} (mov {mov_rilsa}) → CORREGIDO a {destino_inferido}")
            else:
                stats["sin_destino"] += 1
                stats["destino_agregado"] += 1

            # Actualizar destino
            evento["dest_cardinal"] = destino_inferido
            evento["destination_cardinal"] = destino_inferido
        else:
            # Movimiento no mapeado
            stats["movimientos_sin_mapeo"].add((origen, mov_rilsa))
            stats["sin_info_suficiente"] += 1

    # Guardar cambios
    backup_file = data_path / "playback_events.backup.json"
    print(f"\n💾 Creando backup en: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Guardando cambios en: {playback_file}")
    with open(playback_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Convertir set a lista para serialización
    stats["movimientos_sin_mapeo"] = list(stats["movimientos_sin_mapeo"])

    return stats


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python completar_destinos_rilsa.py <dataset_id>")
        print("Ejemplo: python completar_destinos_rilsa.py dataset_f8144347")
        sys.exit(1)

    dataset_id = sys.argv[1]

    print("=" * 70)
    print("🎯 COMPLETAR DESTINATION_CARDINAL USANDO MAPEO RILSA")
    print("=" * 70)
    print(f"\nDataset: {dataset_id}\n")

    stats = completar_destinos(dataset_id)

    if not stats.get("success"):
        print(f"\n❌ Error: {stats.get('error')}")
        sys.exit(1)

    # Mostrar resultados
    print("\n" + "=" * 70)
    print("📊 RESULTADOS")
    print("=" * 70)
    print(f"Total de eventos:              {stats['total_eventos']}")
    print(f"Con destino original válido:   {stats['con_destino_original']}")
    print(f"Sin destino (agregado):        {stats['destino_agregado']}")
    print(f"Destinos corregidos:           {stats['destino_corregido']}")
    print(f"Sin información suficiente:    {stats['sin_info_suficiente']}")

    if stats['movimientos_sin_mapeo']:
        print(f"\n⚠️  Movimientos sin mapeo encontrados:")
        for origen, mov in stats['movimientos_sin_mapeo']:
            print(f"    - Origen: {origen}, Movimiento RILSA: {mov}")

    total_modificados = stats['destino_agregado'] + stats['destino_corregido']
    print(f"\n✅ Se completaron {total_modificados} destinos correctamente")
    print("=" * 70)


if __name__ == "__main__":
    main()
