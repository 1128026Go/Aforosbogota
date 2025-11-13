/**
 * Mapeo de movimientos RILSA según origen y destino
 *
 * Clasificación estándar de movimientos en intersecciones:
 * - 1-3: Giros a la derecha
 * - 4-6: De frente
 * - 7-9: Giros a la izquierda
 * - 10: Retorno (U-turn)
 */

import type { Cardinal } from '../types/aforo';

/**
 * Tabla de mapeo RILSA: origen→destino = movimiento
 * Ajustado según convención colombiana (sentido horario desde Norte)
 */
const RILSA_MAP: Record<string, number> = {
  // Desde Norte (N)
  'N->S': 1,   // Directo
  'N->E': 5,   // Izquierda
  'N->O': 91,  // Derecha 9(1)
  'N->N': 101, // Giro en U 10(1)

  // Desde Sur (S)
  'S->N': 2,   // Directo
  'S->O': 6,   // Izquierda
  'S->E': 92,  // Derecha 9(2)
  'S->S': 102, // Giro en U 10(2)

  // Desde Oeste (O)
  'O->E': 3,   // Directo
  'O->N': 7,   // Izquierda
  'O->S': 93,  // Derecha 9(3)
  'O->O': 103, // Giro en U 10(3)

  // Desde Este (E)
  'E->O': 4,   // Directo
  'E->S': 8,   // Izquierda
  'E->N': 94,  // Derecha 9(4)
  'E->E': 104, // Giro en U 10(4)
};

/**
 * Mapea origen y destino a movimiento RILSA
 * @param origen Punto cardinal de origen
 * @param destino Punto cardinal de destino
 * @returns Número de movimiento RILSA (1-10), o 0 si no se encuentra
 */
export function mapRilsa(origen: Cardinal, destino: Cardinal): number {
  const key = `${origen}->${destino}`;
  return RILSA_MAP[key] ?? 0;
}

/**
 * Descripciones detalladas por código RILSA
 */
const DESCRIPCIONES_RILSA: Record<number, string> = {
  1: 'Norte → Sur (directo)',
  2: 'Sur → Norte (directo)',
  3: 'Oeste → Este (directo)',
  4: 'Este → Oeste (directo)',
  5: 'Norte → Este (izquierda)',
  6: 'Sur → Oeste (izquierda)',
  7: 'Oeste → Norte (izquierda)',
  8: 'Este → Sur (izquierda)',
  91: 'Norte → Oeste (derecha) 9(1)',
  92: 'Sur → Este (derecha) 9(2)',
  93: 'Oeste → Sur (derecha) 9(3)',
  94: 'Este → Norte (derecha) 9(4)',
  101: 'Retorno en Norte 10(1)',
  102: 'Retorno en Sur 10(2)',
  103: 'Retorno en Oeste 10(3)',
  104: 'Retorno en Este 10(4)',
};

/**
 * Obtiene el nombre descriptivo del movimiento
 * @param movRilsa Número de movimiento RILSA
 * @returns Descripción del movimiento
 */
export function getNombreMovimiento(movRilsa: number): string {
  return DESCRIPCIONES_RILSA[movRilsa] ?? `Desconocido (${movRilsa})`;
}

/**
 * Obtiene el emoji representativo del movimiento
 * @param movRilsa Número de movimiento RILSA
 * @returns Emoji del movimiento
 */
export function getEmojiMovimiento(movRilsa: number): string {
  if (movRilsa >= 1 && movRilsa <= 4) return '⬆️';
  if (movRilsa >= 5 && movRilsa <= 8) return '↖️';
  if (movRilsa >= 91 && movRilsa <= 94) return '↗️';
  if (movRilsa >= 101 && movRilsa <= 104) return '↩️';
  return '❓';
}
