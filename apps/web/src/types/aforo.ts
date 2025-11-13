/**
 * Tipos para el sistema de aforo en vivo
 * Conteo por trayectoria (no por frame)
 */

export type ClaseMovil =
  | 'car'        // Automóvil
  | 'truck'      // Camión
  | 'bus'        // Bus
  | 'motorcycle' // Motocicleta
  | 'bicycle'    // Bicicleta
  | 'person';    // Peatón

export type Cardinal = 'N' | 'S' | 'E' | 'O';

export type Periodo = 'mañana' | 'tarde';

/**
 * Evento emitido cuando una trayectoria se completa (egreso del área)
 */
export interface TrajectoryCompletedEvent {
  /** ID del aforo */
  aforoId: string;

  /** ID único del track */
  track_id: string;

  /** Clase del vehículo/persona */
  clase: ClaseMovil;

  /** Timestamp de salida en formato ISO 8601 */
  t_exit_iso: string;

  /** Punto cardinal de origen (ya calculado por JSON de accesos) */
  origin_cardinal: Cardinal;

  /** Punto cardinal de destino (ya calculado por JSON de accesos) */
  dest_cardinal: Cardinal;

  /** Movimiento RILSA (1-8, 91-94, 101-104) basado en origen→destino */
  mov_rilsa: number;

  /** Ramal (usa origin_cardinal) */
  ramal: Cardinal;

  /** Velocidad mediana de la trayectoria (opcional) */
  v_kmh_mediana?: number;
}

/**
 * Clave para bucket de 15 minutos
 */
export interface BucketKey {
  /** Timestamp de inicio del bucket (ISO 8601) */
  bucket_iso: string;

  /** Periodo del día */
  periodo: Periodo;

  /** Ramal */
  ramal: Cardinal;
}

/**
 * Clave para conteo específico
 */
export interface CountKey {
  /** Movimiento RILSA (1-8, 91-94, 101-104) */
  movimiento_rilsa: number;

  /** Clase del móvil */
  clase: ClaseMovil;
}

/**
 * Datos de un bucket de 15 minutos
 */
export interface BucketData {
  /** Clave del bucket */
  key: BucketKey;

  /** Conteos por movimiento y clase */
  counts: Record<string, number>;

  /** Total de trayectorias en el bucket */
  total: number;

  /** Timestamp de inicio del bucket */
  start: Date;

  /** Timestamp de fin del bucket */
  end: Date;
}

/**
 * Registro para exportación CSV
 */
export interface AforoCSVRecord {
  timestamp_inicio: string;
  periodo: Periodo;
  ramal: Cardinal;
  movimiento_rilsa: number;
  clase: ClaseMovil;
  conteo: number;
}

/**
 * Categorías de vehículos para tablas de volúmenes
 * (agrupaciones de ClaseMovil)
 */
export type CategoriaVehicular = 'autos' | 'buses' | 'camiones' | 'motos' | 'bicicletas' | 'peatones';

/**
 * Conteos por categoría para un intervalo de 15 minutos
 */
export interface ConteosPorCategoria {
  autos: number;
  buses: number;
  camiones: number;
  motos: number;
  bicicletas: number;
  peatones: number;
}

/**
 * Fila de la tabla de volúmenes (intervalo de 15 minutos)
 */
export interface FilaVolumen extends ConteosPorCategoria {
  /** Periodo de tiempo, ej: "06:00 - 06:15" */
  periodo: string;

  /** Timestamp de inicio del intervalo */
  timestamp_inicio: string;
}

/**
 * Información de un movimiento RILSA
 */
export interface MovimientoRilsa {
  /** Código del movimiento (1-8, 91-94, 101-104) */
  codigo: number;

  /** Punto cardinal de origen */
  origen: Cardinal;

  /** Punto cardinal de destino */
  destino: Cardinal;

  /** Nombre descriptivo, ej: "N → S" */
  nombre: string;

  /** Tipo de movimiento */
  tipo: 'recto' | 'giro_izquierda' | 'giro_derecha' | 'retorno_u';

  /** Datos de volúmenes por intervalo */
  filas: FilaVolumen[];

  /** Totales por categoría */
  totales: ConteosPorCategoria;
}

/**
 * Datos completos de aforo por movimientos
 */
export interface DatosAforoPorMovimiento {
  /** Metadatos del aforo */
  metadata: {
    ubicacion: string;
    fecha: string; // Formato largo en español
    fecha_iso: string; // Formato ISO para procesamiento
    hora_inicio: string;
    hora_fin: string;
  };

  /** Volúmenes totales (todos los movimientos combinados) */
  volumenes_totales: {
    filas: FilaVolumen[];
    totales: ConteosPorCategoria;
  };

  /** Movimientos individuales (solo los que tienen datos) */
  movimientos: Record<number, MovimientoRilsa>;
}

/**
 * Mapeo de códigos RILSA a nombres descriptivos
 * Basado en la nomenclatura estándar RILSA para intersecciones de 4 accesos
 */
export const MOVIMIENTOS_RILSA_NOMBRES: Record<number, { nombre: string; tipo: MovimientoRilsa['tipo'] }> = {
  // Movimientos directos (1-4)
  1: { nombre: 'N → S', tipo: 'recto' },
  2: { nombre: 'S → N', tipo: 'recto' },
  3: { nombre: 'O → E', tipo: 'recto' },
  4: { nombre: 'E → O', tipo: 'recto' },

  // Giros a la izquierda (5-8)
  5: { nombre: 'N → E', tipo: 'giro_izquierda' },
  6: { nombre: 'S → O', tipo: 'giro_izquierda' },
  7: { nombre: 'O → N', tipo: 'giro_izquierda' },
  8: { nombre: 'E → S', tipo: 'giro_izquierda' },

  // Giros a la derecha (91-94)
  91: { nombre: 'N → O', tipo: 'giro_derecha' },  // 9(1)
  92: { nombre: 'S → E', tipo: 'giro_derecha' },  // 9(2)
  93: { nombre: 'O → S', tipo: 'giro_derecha' },  // 9(3)
  94: { nombre: 'E → N', tipo: 'giro_derecha' },  // 9(4)

  // Giros en U (101-104)
  101: { nombre: 'U-turn Norte', tipo: 'retorno_u' },   // 10(1)
  102: { nombre: 'U-turn Sur', tipo: 'retorno_u' },     // 10(2)
  103: { nombre: 'U-turn Oeste', tipo: 'retorno_u' },   // 10(3)
  104: { nombre: 'U-turn Este', tipo: 'retorno_u' },    // 10(4)
};
