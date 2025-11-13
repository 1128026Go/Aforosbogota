"""
Simulador de Trayectorias Completadas
Procesa detecciones del PKL y simula vehículos completando trayectorias
para demostrar el sistema de aforo en vivo
"""

import pickle
import requests
import random
from datetime import datetime, timedelta
from pathlib import Path
import json
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def simular_trayectorias_completadas(dataset_id: str, num_trayectorias: int = 50):
    """
    Simula trayectorias completadas enviándolas al endpoint de aforo
    """

    # Cargar configuración de cardinales
    data_dir = Path("api/data") / dataset_id
    cardinals_file = data_dir / "cardinals.json"

    if not cardinals_file.exists():
        print("❌ No hay cardinales configurados. Configura los accesos primero.")
        return

    cardinals_data = json.loads(cardinals_file.read_text())
    accesses = cardinals_data.get("accesses", [])

    if len(accesses) < 2:
        print("❌ Se requieren al menos 2 accesos configurados")
        return

    print(f"✓ Cardinales cargados: {len(accesses)} accesos")
    for acc in accesses:
        print(f"  - {acc['name']} ({acc['cardinal']})")

    # Cargar mapa RILSA
    rilsa_file = data_dir / "rilsa_map.json"
    if not rilsa_file.exists():
        print("❌ No hay mapa RILSA configurado.")
        return

    rilsa_data = json.loads(rilsa_file.read_text())
    rules = rilsa_data.get("rules", {})
    print(f"✓ Mapa RILSA cargado: {len(rules)} movimientos")

    # Clases de vehículos
    clases = ["car", "motorcycle", "bus", "truck_c1", "truck_c2", "bicycle", "person"]

    # Tiempo base (ahora - 2 horas)
    base_time = datetime.now() - timedelta(hours=2)

    print(f"\n🚗 Simulando {num_trayectorias} trayectorias completadas...")

    exitos = 0
    errores = 0

    for i in range(num_trayectorias):
        # Seleccionar origen y destino aleatorios
        origin_access = random.choice(accesses)
        dest_access = random.choice([a for a in accesses if a['id'] != origin_access['id']])

        # Calcular tiempo de salida (distribuido en las últimas 2 horas)
        t_exit = base_time + timedelta(seconds=random.randint(0, 7200))

        # Generar ID de track único
        track_id = f"track_{dataset_id}_{i}_{random.randint(1000, 9999)}"

        # Seleccionar clase aleatoria (más probabilidad para autos)
        weights = [0.5, 0.2, 0.05, 0.05, 0.05, 0.1, 0.05]
        clase = random.choices(clases, weights=weights)[0]

        # Preparar payload
        payload = {
            "track_id": track_id,
            "clase": clase,
            "t_exit_iso": t_exit.isoformat(),
            "origin_access": origin_access['id'],
            "dest_access": dest_access['id'],
        }

        # Enviar al backend
        try:
            response = requests.post(
                f"http://localhost:3004/api/aforos/{dataset_id}/track-completed",
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                exitos += 1
                data = response.json()
                print(f"  ✓ [{i+1}/{num_trayectorias}] {clase:12} | {origin_access['cardinal']} → {dest_access['cardinal']} | RILSA {data.get('mov_rilsa', '?'):2} | {t_exit.strftime('%H:%M:%S')}")
            else:
                errores += 1
                print(f"  ✗ [{i+1}/{num_trayectorias}] Error {response.status_code}: {response.text[:100]}")

        except Exception as e:
            errores += 1
            print(f"  ✗ [{i+1}/{num_trayectorias}] Error: {str(e)[:100]}")

    print(f"\n✅ Simulación completa:")
    print(f"   - Exitosas: {exitos}")
    print(f"   - Errores: {errores}")
    print(f"\n💡 Ahora recarga la página web y ve al Paso 3 para ver los conteos!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python simular_trayectorias.py <dataset_id> [num_trayectorias]")
        print("\nEjemplo:")
        print("  python simular_trayectorias.py dataset_f8144347 100")
        sys.exit(1)

    dataset_id = sys.argv[1]
    num_trayectorias = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    simular_trayectorias_completadas(dataset_id, num_trayectorias)
