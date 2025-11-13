"""
Script para aplicar las correcciones sugeridas al archivo trajectory_corrections.json

Este script toma las sugerencias generadas por analyze_misclassifications.py
y las aplica automáticamente, generando correcciones que se usarán al
reprocesar el playback.
"""
import json
from pathlib import Path
from datetime import datetime

def apply_suggestions(dataset_id='dataset_f8144347', confidence_filter='all'):
    """
    Aplica las sugerencias de reclasificación

    Args:
        dataset_id: ID del dataset
        confidence_filter: 'all', 'medium', 'high' - filtro por confianza
    """
    data_dir = Path('data') / dataset_id
    suggestions_file = data_dir / 'reclassification_suggestions.json'
    corrections_file = data_dir / 'trajectory_corrections.json'

    # Cargar sugerencias
    print(">> Cargando sugerencias...")
    suggestions = json.load(open(suggestions_file, encoding='utf-8'))

    # Cargar correcciones existentes
    if corrections_file.exists():
        corrections = json.load(open(corrections_file, encoding='utf-8'))
    else:
        corrections = {
            "corrections": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_corrections": 0,
                "last_updated": datetime.now().isoformat()
            }
        }

    # Filtrar por confianza si es necesario
    filtered_suggestions = suggestions['suggestions']
    if confidence_filter == 'medium':
        filtered_suggestions = [s for s in filtered_suggestions if s['confidence'] == 'medium']
    elif confidence_filter == 'high':
        filtered_suggestions = [s for s in filtered_suggestions if s['confidence'] == 'high']

    print(f"\n>> Aplicando {len(filtered_suggestions)} correcciones...")
    print(f"   Filtro de confianza: {confidence_filter}")

    # Contar por tipo
    by_type = {}
    applied = 0
    skipped_existing = 0

    for suggestion in filtered_suggestions:
        track_id = suggestion['track_id']
        suggested_class = suggestion['suggested_class']

        # Verificar si ya existe una corrección manual
        if track_id in corrections['corrections']:
            # No sobrescribir correcciones manuales
            skipped_existing += 1
            continue

        # Aplicar corrección automática
        corrections['corrections'][track_id] = {
            'new_origin': None,  # No cambiamos origen/destino
            'new_dest': None,
            'new_class': suggested_class,
            'discard': False,
            'timestamp': datetime.now().isoformat(),
            'auto_generated': True,
            'spread_area': suggestion['spread_area'],
            'confidence': suggestion['confidence']
        }

        by_type[suggested_class] = by_type.get(suggested_class, 0) + 1
        applied += 1

    # Actualizar metadata
    corrections['metadata']['total_corrections'] = len(corrections['corrections'])
    corrections['metadata']['last_updated'] = datetime.now().isoformat()
    corrections['metadata']['auto_corrections'] = applied
    corrections['metadata']['thresholds_used'] = suggestions['thresholds']

    # Guardar
    with open(corrections_file, 'w', encoding='utf-8') as f:
        json.dump(corrections, f, indent=2, ensure_ascii=False)

    print(f"\n>> RESULTADO:")
    print(f"   Correcciones aplicadas: {applied}")
    print(f"   Correcciones manuales preservadas: {skipped_existing}")
    print(f"\n   Desglose por clase:")
    for clase, count in sorted(by_type.items()):
        print(f"     {clase}: {count}")

    print(f"\n>> Archivo actualizado: {corrections_file}")
    print(f"   Total correcciones en archivo: {corrections['metadata']['total_corrections']}")

    print("\n>> SIGUIENTE PASO:")
    print("   Reprocesa el playback para aplicar estas correcciones:")
    print("   POST http://localhost:3003/api/datasets/dataset_f8144347/process-playback")

    return corrections

if __name__ == '__main__':
    import sys

    # Permitir especificar filtro de confianza como argumento
    confidence = 'all'
    if len(sys.argv) > 1:
        confidence = sys.argv[1]

    print("=" * 80)
    print("APLICADOR DE CORRECCIONES AUTOMATICAS")
    print("=" * 80)
    print(f"\nEste script aplicara las correcciones sugeridas por el analisis.")
    print(f"Filtro de confianza: {confidence}")
    print("\nPresiona Ctrl+C para cancelar o Enter para continuar...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\nCancelado por el usuario.")
        sys.exit(0)

    corrections = apply_suggestions(confidence_filter=confidence)

    print("\n>> LISTO! Las correcciones han sido aplicadas.")
    print("   Ahora necesitas reprocesar el playback para que se reflejen en los aforos.")
