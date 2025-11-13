"""
Script para validar y corregir destination_cardinal usando el mapeo RILSA

Verifica que cada evento tenga el destination_cardinal correcto según:
- origin_cardinal + mov_rilsa

Reporta y corrige cualquier inconsistencia encontrada.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import sys

# Mapeo RILSA completo: (origen, mov_rilsa) -> destino
MAPEO_RILSA_DESTINO = {
    # Directos (1-4)
    ('N', 1): 'S',   ('S', 2): 'N',   ('O', 3): 'E',   ('E', 4): 'O',
    # Izquierdas (5-8)
    ('N', 5): 'E',   ('S', 6): 'O',   ('O', 7): 'N',   ('E', 8): 'S',
    # Derechas (91-94)
    ('N', 91): 'O',  ('S', 92): 'E',  ('O', 93): 'S',  ('E', 94): 'N',
    # U-turns (101-104)
    ('N', 101): 'N', ('S', 102): 'S', ('O', 103): 'O', ('E', 104): 'E',
}

# Mapeo inverso: mov_rilsa -> nombre legible
NOMBRES_MOVIMIENTOS = {
    1: "N→S (Directo)", 2: "S→N (Directo)", 3: "O→E (Directo)", 4: "E→O (Directo)",
    5: "N→E (Izq)", 6: "S→O (Izq)", 7: "O→N (Izq)", 8: "E→S (Izq)",
    91: "N→O (Der)", 92: "S→E (Der)", 93: "O→S (Der)", 94: "E→N (Der)",
    101: "N→N (U-turn)", 102: "S→S (U-turn)", 103: "O→O (U-turn)", 104: "E→E (U-turn)",
}


def validar_y_corregir_destinos(dataset_id: str, auto_corregir: bool = False, base_path: str = "data") -> Dict:
    """
    Valida y opcionalmente corrige los destination_cardinal según mapeo RILSA.

    Args:
        dataset_id: ID del dataset
        auto_corregir: Si True, corrige automáticamente las inconsistencias
        base_path: Ruta base de datos

    Returns:
        Dict con estadísticas y lista de inconsistencias
    """
    script_dir = Path(__file__).parent.parent
    data_path = script_dir / base_path / dataset_id
    playback_file = data_path / "playback_events.json"

    if not playback_file.exists():
        return {"error": f"No se encontró {playback_file}", "success": False}

    print(f"📂 Analizando: {playback_file}")

    with open(playback_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    eventos = data.get("events", [])

    stats = {
        "total_eventos": len(eventos),
        "consistentes": 0,
        "inconsistentes": 0,
        "sin_origen": 0,
        "sin_movimiento": 0,
        "sin_destino_original": 0,
        "movimiento_desconocido": 0,
        "corregidos": 0,
        "inconsistencias": [],
        "success": True
    }

    for i, evento in enumerate(eventos):
        track_id = evento.get("track_id", f"evento_{i}")
        origen = evento.get("origin_cardinal")
        mov_rilsa = evento.get("mov_rilsa")
        dest_actual = evento.get("dest_cardinal") or evento.get("destination_cardinal")

        # Verificar datos completos
        if not origen:
            stats["sin_origen"] += 1
            continue

        if mov_rilsa is None:
            stats["sin_movimiento"] += 1
            continue

        # Obtener destino esperado según RILSA
        destino_esperado = MAPEO_RILSA_DESTINO.get((origen, mov_rilsa))

        if not destino_esperado:
            stats["movimiento_desconocido"] += 1
            stats["inconsistencias"].append({
                "track_id": track_id,
                "tipo": "MOVIMIENTO_NO_MAPEADO",
                "origen": origen,
                "mov_rilsa": mov_rilsa,
                "dest_actual": dest_actual,
                "descripcion": f"Movimiento RILSA {mov_rilsa} desde {origen} no está en el mapeo"
            })
            continue

        # Verificar consistencia
        if not dest_actual:
            stats["sin_destino_original"] += 1
            if auto_corregir:
                evento["dest_cardinal"] = destino_esperado
                evento["destination_cardinal"] = destino_esperado
                stats["corregidos"] += 1
            stats["inconsistencias"].append({
                "track_id": track_id,
                "tipo": "SIN_DESTINO",
                "origen": origen,
                "mov_rilsa": mov_rilsa,
                "movimiento": NOMBRES_MOVIMIENTOS.get(mov_rilsa, f"Mov {mov_rilsa}"),
                "dest_esperado": destino_esperado,
                "dest_actual": None,
                "corregido": auto_corregir
            })
        elif dest_actual != destino_esperado:
            stats["inconsistentes"] += 1
            if auto_corregir:
                evento["dest_cardinal"] = destino_esperado
                evento["destination_cardinal"] = destino_esperado
                stats["corregidos"] += 1
            stats["inconsistencias"].append({
                "track_id": track_id,
                "tipo": "INCONSISTENTE",
                "origen": origen,
                "mov_rilsa": mov_rilsa,
                "movimiento": NOMBRES_MOVIMIENTOS.get(mov_rilsa, f"Mov {mov_rilsa}"),
                "dest_esperado": destino_esperado,
                "dest_actual": dest_actual,
                "corregido": auto_corregir
            })
        else:
            stats["consistentes"] += 1

    # Guardar si se hicieron correcciones
    if auto_corregir and stats["corregidos"] > 0:
        backup_file = data_path / "playback_events.backup_validacion.json"
        print(f"\n💾 Creando backup en: {backup_file}")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 Guardando correcciones en: {playback_file}")
        with open(playback_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return stats


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python validar_destinos_rilsa.py <dataset_id> [--fix]")
        print("Ejemplo (solo validar): python validar_destinos_rilsa.py dataset_f8144347")
        print("Ejemplo (validar y corregir): python validar_destinos_rilsa.py dataset_f8144347 --fix")
        sys.exit(1)

    dataset_id = sys.argv[1]
    auto_corregir = "--fix" in sys.argv

    print("=" * 70)
    print("🔍 VALIDAR DESTINATION_CARDINAL USANDO MAPEO RILSA")
    print("=" * 70)
    print(f"\nDataset: {dataset_id}")
    print(f"Modo: {'CORREGIR AUTOMÁTICAMENTE' if auto_corregir else 'SOLO VALIDAR'}\n")

    stats = validar_y_corregir_destinos(dataset_id, auto_corregir)

    if not stats.get("success"):
        print(f"\n❌ Error: {stats.get('error')}")
        sys.exit(1)

    # Mostrar resultados
    print("\n" + "=" * 70)
    print("📊 RESULTADOS")
    print("=" * 70)
    print(f"Total de eventos:              {stats['total_eventos']}")
    print(f"✅ Consistentes:               {stats['consistentes']}")
    print(f"❌ Inconsistentes:             {stats['inconsistentes']}")
    print(f"⚠️  Sin destino original:      {stats['sin_destino_original']}")
    print(f"   Sin origen:                 {stats['sin_origen']}")
    print(f"   Sin movimiento RILSA:       {stats['sin_movimiento']}")
    print(f"   Movimiento desconocido:     {stats['movimiento_desconocido']}")

    if auto_corregir:
        print(f"\n🔧 Eventos corregidos:         {stats['corregidos']}")

    # Mostrar inconsistencias detalladas
    if stats["inconsistencias"]:
        print(f"\n⚠️  INCONSISTENCIAS ENCONTRADAS: {len(stats['inconsistencias'])}")
        print("-" * 70)

        # Agrupar por tipo
        por_tipo = {}
        for inc in stats["inconsistencias"]:
            tipo = inc["tipo"]
            por_tipo.setdefault(tipo, []).append(inc)

        for tipo, items in por_tipo.items():
            print(f"\n{tipo}: {len(items)} casos")
            for inc in items[:10]:  # Mostrar solo primeros 10 de cada tipo
                if tipo == "INCONSISTENTE":
                    print(f"  • Track {inc['track_id']}: {inc['movimiento']}")
                    print(f"    Esperado: {inc['dest_esperado']}, Actual: {inc['dest_actual']}")
                    if inc.get("corregido"):
                        print(f"    ✅ CORREGIDO")
                elif tipo == "SIN_DESTINO":
                    print(f"  • Track {inc['track_id']}: {inc['movimiento']}")
                    print(f"    Debería ser: {inc['dest_esperado']}")
                    if inc.get("corregido"):
                        print(f"    ✅ AGREGADO")
                elif tipo == "MOVIMIENTO_NO_MAPEADO":
                    print(f"  • Track {inc['track_id']}: Origen={inc['origen']}, Mov={inc['mov_rilsa']}")

            if len(items) > 10:
                print(f"  ... y {len(items) - 10} más")

    if stats["inconsistentes"] > 0 or stats["sin_destino_original"] > 0:
        if not auto_corregir:
            print(f"\n💡 Ejecuta con --fix para corregir automáticamente")
    else:
        print(f"\n✅ Todos los destinos son consistentes con el mapeo RILSA")

    print("=" * 70)


if __name__ == "__main__":
    main()
