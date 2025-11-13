/**
 * Utilidades para procesar eventos de aforo en vivo
 * Convierte eventos de PlaybackEvent a estructura DatosAforoPorMovimiento
 */

import type { DatosAforoPorMovimiento, FilaVolumen, ConteosPorCategoria, MovimientoRilsa } from '@/types/aforo';
import { MOVIMIENTOS_RILSA_NOMBRES } from '@/types/aforo';

interface PlaybackEvent {
  track_id: string;
  class: string;
  frame_entry: number;
  frame_exit: number;
  timestamp_entry: string;
  timestamp_exit: string;
  origin_access: string;
  dest_access: string;
  origin_cardinal: string;
  dest_cardinal: string;
  mov_rilsa: number;
  positions: [number, number][];
  confidence: number;
}

/**
 * Clasificar vehículo de evento a categoría
 */
function clasificarEventoVehiculo(clase: string): keyof ConteosPorCategoria | null {
  switch (clase) {
    case 'car':
      return 'autos';
    case 'bus':
      return 'buses';
    case 'truck':
      return 'camiones';
    case 'motorcycle':
      return 'motos';
    case 'bicycle':
      return 'bicicletas';
    case 'person':
      return 'peatones';
    default:
      return null;
  }
}

/**
 * Crear fila vacía
 */
function crearFilaVacia(periodo: string, timestamp_inicio: string): FilaVolumen {
  return {
    periodo,
    timestamp_inicio,
    autos: 0,
    buses: 0,
    camiones: 0,
    motos: 0,
    bicicletas: 0,
    peatones: 0,
  };
}

/**
 * Crear conteos vacíos
 */
function crearConteosVacios(): ConteosPorCategoria {
  return {
    autos: 0,
    buses: 0,
    camiones: 0,
    motos: 0,
    bicicletas: 0,
    peatones: 0,
  };
}

/**
 * Formatear periodo
 */
function formatearPeriodo(timestamp: string): string {
  const fecha = new Date(timestamp);
  const horaInicio = fecha.toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  const fechaFin = new Date(fecha.getTime() + 15 * 60 * 1000);
  const horaFin = fechaFin.toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  return `${horaInicio} - ${horaFin}`;
}

/**
 * Procesa eventos de playback en vivo y genera datos de aforo por movimiento
 */
export function procesarEventosEnVivo(
  eventos: PlaybackEvent[],
  metadata?: {
    ubicacion?: string;
    fecha?: string;
  }
): DatosAforoPorMovimiento {
  if (!eventos || eventos.length === 0) {
    // Retornar estructura vacía
    return {
      metadata: {
        ubicacion: metadata?.ubicacion || 'Sin especificar',
        fecha: metadata?.fecha || new Date().toLocaleDateString('es-CO', {
          day: 'numeric',
          month: 'long',
          year: 'numeric',
        }),
        fecha_iso: new Date().toISOString().split('T')[0],
        hora_inicio: '00:00',
        hora_fin: '00:00',
      },
      volumenes_totales: {
        filas: [],
        totales: crearConteosVacios(),
      },
      movimientos: {},
    };
  }

  // Agrupar eventos por intervalos de 15 minutos usando timestamp_exit
  const intervalosMap = new Map<string, Map<number, Map<string, number>>>();

  eventos.forEach((evento) => {
    const categoria = clasificarEventoVehiculo(evento.class);
    if (!categoria) return; // Ignorar peatones

    const exitDate = new Date(evento.timestamp_exit);
    const intervalStart = new Date(exitDate);
    intervalStart.setMinutes(Math.floor(intervalStart.getMinutes() / 15) * 15, 0, 0);
    const intervalKey = intervalStart.toISOString().substring(0, 16);

    if (!intervalosMap.has(intervalKey)) {
      intervalosMap.set(intervalKey, new Map());
    }

    const movimientos = intervalosMap.get(intervalKey)!;
    if (!movimientos.has(evento.mov_rilsa)) {
      movimientos.set(evento.mov_rilsa, new Map());
    }

    const categorias = movimientos.get(evento.mov_rilsa)!;
    categorias.set(categoria, (categorias.get(categoria) || 0) + 1);
  });

  // Obtener timestamps ordenados
  const timestamps = Array.from(intervalosMap.keys()).sort();

  // Construir volúmenes totales
  const conteosTotales = new Map<string, FilaVolumen>();
  timestamps.forEach((ts) => {
    const periodo = formatearPeriodo(ts);
    conteosTotales.set(ts, crearFilaVacia(periodo, ts));
  });

  // Construir datos por movimiento
  const conteosPorMovimiento = new Map<number, Map<string, FilaVolumen>>();

  intervalosMap.forEach((movimientos, timestamp) => {
    movimientos.forEach((categorias, codigoMov) => {
      // Inicializar movimiento si no existe
      if (!conteosPorMovimiento.has(codigoMov)) {
        conteosPorMovimiento.set(codigoMov, new Map());
        timestamps.forEach((ts) => {
          const periodo = formatearPeriodo(ts);
          conteosPorMovimiento.get(codigoMov)!.set(ts, crearFilaVacia(periodo, ts));
        });
      }

      const filaMovimiento = conteosPorMovimiento.get(codigoMov)!.get(timestamp)!;
      const filaTotales = conteosTotales.get(timestamp)!;

      categorias.forEach((count, categoria) => {
        filaMovimiento[categoria] += count;
        filaTotales[categoria] += count;
      });
    });
  });

  // Calcular totales globales
  const totalesGlobales = crearConteosVacios();
  const filasTotales = Array.from(conteosTotales.values());
  filasTotales.forEach((fila) => {
    totalesGlobales.autos += fila.autos;
    totalesGlobales.buses += fila.buses;
    totalesGlobales.camiones += fila.camiones;
    totalesGlobales.motos += fila.motos;
    totalesGlobales.bicicletas += fila.bicicletas;
    totalesGlobales.peatones += fila.peatones;
  });

  // Construir movimientos
  const movimientos: Record<number, MovimientoRilsa> = {};

  conteosPorMovimiento.forEach((intervalos, codigoMov) => {
    const filas = Array.from(intervalos.values());
    const totales = crearConteosVacios();

    filas.forEach((fila) => {
      totales.autos += fila.autos;
      totales.buses += fila.buses;
      totales.camiones += fila.camiones;
      totales.motos += fila.motos;
      totales.bicicletas += fila.bicicletas;
      totales.peatones += fila.peatones;
    });

    const tieneDatos = totales.autos + totales.buses + totales.camiones + totales.motos + totales.bicicletas + totales.peatones > 0;

    if (tieneDatos) {
      const info = MOVIMIENTOS_RILSA_NOMBRES[codigoMov] || {
        nombre: `Movimiento ${codigoMov}`,
        tipo: 'recto' as const,
      };

      // Determinar origen y destino
      const match = info.nombre.match(/([NSEO])\s*→\s*([NSEO])/);
      const origen = (match?.[1] || 'N') as any;
      const destino = (match?.[2] || 'S') as any;

      movimientos[codigoMov] = {
        codigo: codigoMov,
        origen,
        destino,
        nombre: info.nombre,
        tipo: info.tipo,
        filas,
        totales,
      };
    }
  });

  // Extraer horas
  const horaInicio = timestamps[0]?.substring(11, 16) || '00:00';
  const horaFin = timestamps[timestamps.length - 1]?.substring(11, 16) || '00:00';

  return {
    metadata: {
      ubicacion: metadata?.ubicacion || 'En vivo',
      fecha: metadata?.fecha || new Date().toLocaleDateString('es-CO', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      }),
      fecha_iso: new Date().toISOString().split('T')[0],
      hora_inicio: horaInicio,
      hora_fin: horaFin,
    },
    volumenes_totales: {
      filas: filasTotales,
      totales: totalesGlobales,
    },
    movimientos,
  };
}

/**
 * Filtra eventos hasta un frame específico (para reproducción)
 */
export function procesarEventosHastaFrame(
  eventos: PlaybackEvent[],
  frameActual: number,
  metadata?: {
    ubicacion?: string;
    fecha?: string;
  }
): DatosAforoPorMovimiento {
  const eventosFiltrados = eventos.filter((e) => e.frame_exit <= frameActual);
  return procesarEventosEnVivo(eventosFiltrados, metadata);
}
