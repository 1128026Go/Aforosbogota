import { MOVIMIENTOS_RILSA_NOMBRES, type MovimientoRilsa } from '@/types/aforo';

const PERSON_CLASSES = new Set(['person', 'pedestrian', 'peaton']);

export function isPersona(clase?: string | null): boolean {
  if (!clase) return false;
  return PERSON_CLASSES.has(clase.toLowerCase());
}

/**
 * Obtiene un nombre limpio (ASCII) para un movimiento RILSA.
 * Si no hay nombre en catálogo, construye uno con origen/destino.
 */
export function obtenerNombreMovimiento(
  movimiento: Pick<MovimientoRilsa, 'codigo' | 'nombre' | 'origen' | 'destino'>
): string {
  const nombreCatalogo = MOVIMIENTOS_RILSA_NOMBRES[movimiento.codigo]?.nombre;
  if (nombreCatalogo) {
    return sanitizarNombre(nombreCatalogo);
  }

  if (movimiento.nombre && movimiento.nombre.trim().length > 0) {
    return sanitizarNombre(movimiento.nombre);
  }

  if (movimiento.origen && movimiento.destino) {
    return `${movimiento.origen} -> ${movimiento.destino}`;
  }

  return `Movimiento ${movimiento.codigo}`;
}

/**
 * Devuelve una descripción breve según el tipo de movimiento RILSA.
 */
export function obtenerDescripcionMovimiento(tipo?: MovimientoRilsaTipo): string | undefined {
  if (!tipo) return undefined;
  switch (tipo) {
    case 'recto':
      return 'Recto';
    case 'giro_izquierda':
      return 'Giro izquierda';
    case 'giro_derecha':
      return 'Giro derecha';
    case 'retorno_u':
      return 'Retorno en U';
    default:
      return undefined;
  }
}

function sanitizarNombre(nombre: string): string {
  return nombre
    .replace(/→/g, '->')
    .replace(/↔/g, '<->')
    .replace(/[’‘]/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

type MovimientoRilsaTipo = MovimientoRilsa['tipo'];


