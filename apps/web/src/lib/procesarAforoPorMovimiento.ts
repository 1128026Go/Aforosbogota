/**
 * Utilidades para procesar datos de aforo y generar tablas por movimiento RILSA
 */

import type {
  AforoCSVRecord,
  ClaseMovil,
  ConteosPorCategoria,
  FilaVolumen,
  MovimientoRilsa,
  DatosAforoPorMovimiento,
  Cardinal,
} from '@/types/aforo';
import { MOVIMIENTOS_RILSA_NOMBRES } from '@/types/aforo';

/**
 * Clasifica una clase de vehículo en su categoría correspondiente
 */
function clasificarVehiculo(clase: ClaseMovil): keyof ConteosPorCategoria | null {
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
 * Crea una fila de volumen vacía
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
 * Crea conteos por categoría vacíos
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
 * Formatea un timestamp a formato de periodo "HH:MM - HH:MM"
 */
function formatearPeriodo(timestamp: string): string {
  const fecha = new Date(timestamp);
  const horaInicio = fecha.toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  const fechaFin = new Date(fecha.getTime() + 15 * 60 * 1000); // +15 minutos
  const horaFin = fechaFin.toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  return `${horaInicio} - ${horaFin}`;
}

/**
 * Formatea una fecha en formato largo en español
 */
function formatearFechaLarga(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-CO', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

/**
 * Procesa datos CSV de aforo y genera la estructura para visualización por movimientos
 */
export function procesarDatosAforoPorMovimiento(
  registros: AforoCSVRecord[],
  metadata?: {
    ubicacion?: string;
    fecha?: string;
  }
): DatosAforoPorMovimiento {
  if (!registros || registros.length === 0) {
    throw new Error('No hay datos para procesar');
  }

  // Extraer metadata
  const primerRegistro = registros[0];

  // Validar que el primer registro tenga los campos necesarios
  if (!primerRegistro || !primerRegistro.timestamp_inicio) {
    throw new Error('El formato del CSV es incorrecto. Falta el campo timestamp_inicio');
  }

  const ultimoRegistro = registros[registros.length - 1];

  const fechaISO = primerRegistro.timestamp_inicio.split(' ')[0];
  const ubicacion = metadata?.ubicacion || 'Sin especificar';
  const fechaLarga = metadata?.fecha || formatearFechaLarga(primerRegistro.timestamp_inicio);

  // Extraer timestamps únicos para intervalos de 15 min
  const timestampsSet = new Set<string>();
  registros.forEach((r) => timestampsSet.add(r.timestamp_inicio));
  const timestamps = Array.from(timestampsSet).sort();

  // Mapas para almacenar conteos por movimiento y timestamp
  const conteosPorMovimiento = new Map<number, Map<string, FilaVolumen>>();
  const conteosTotales = new Map<string, FilaVolumen>();

  // Inicializar intervalos
  timestamps.forEach((ts) => {
    const periodo = formatearPeriodo(ts);
    conteosTotales.set(ts, crearFilaVacia(periodo, ts));
  });

  // Procesar cada registro
  registros.forEach((registro) => {
    const categoria = clasificarVehiculo(registro.clase);
    if (!categoria) return; // Ignorar peatones y clases no vehiculares

    const { timestamp_inicio, movimiento_rilsa, conteo } = registro;

    // Actualizar totales
    const filaTotales = conteosTotales.get(timestamp_inicio);
    if (filaTotales) {
      filaTotales[categoria] += conteo;
    }

    // Actualizar por movimiento
    if (!conteosPorMovimiento.has(movimiento_rilsa)) {
      conteosPorMovimiento.set(movimiento_rilsa, new Map());

      // Inicializar todos los intervalos para este movimiento
      timestamps.forEach((ts) => {
        const periodo = formatearPeriodo(ts);
        conteosPorMovimiento.get(movimiento_rilsa)!.set(ts, crearFilaVacia(periodo, ts));
      });
    }

    const filaMovimiento = conteosPorMovimiento.get(movimiento_rilsa)!.get(timestamp_inicio);
    if (filaMovimiento) {
      filaMovimiento[categoria] += conteo;
    }
  });

  // Calcular totales por categoría
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

    // Solo incluir movimientos con datos
    const tieneDatos = totales.autos + totales.buses + totales.camiones + totales.motos + totales.bicicletas + totales.peatones > 0;

    if (tieneDatos) {
      const info = MOVIMIENTOS_RILSA_NOMBRES[codigoMov] || {
        nombre: `Movimiento ${codigoMov}`,
        tipo: 'recto' as const
      };

      // Intentar determinar origen y destino del nombre
      const match = info.nombre.match(/([NSEO])\s*→\s*([NSEO])/);
      const origen = (match?.[1] || 'N') as Cardinal;
      const destino = (match?.[2] || 'S') as Cardinal;

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

  // Extraer horas de inicio y fin
  const horaInicio = timestamps[0]?.split(' ')[1]?.substring(0, 5) || '00:00';
  const horaFin = timestamps[timestamps.length - 1]?.split(' ')[1]?.substring(0, 5) || '23:59';

  return {
    metadata: {
      ubicacion,
      fecha: fechaLarga,
      fecha_iso: fechaISO,
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
 * Carga y procesa un archivo CSV de volúmenes por movimiento
 */
export async function cargarYProcesarCSV(
  archivoCSV: File | string,
  metadata?: { ubicacion?: string; fecha?: string }
): Promise<DatosAforoPorMovimiento> {
  let contenidoCSV: string;

  try {
    if (typeof archivoCSV === 'string') {
      // Es una URL o path
      console.log('Cargando CSV desde:', archivoCSV);
      const response = await fetch(archivoCSV);

      if (!response.ok) {
        throw new Error(`Error al cargar CSV: ${response.status} ${response.statusText}`);
      }

      contenidoCSV = await response.text();
      console.log('CSV cargado, tamaño:', contenidoCSV.length, 'caracteres');
    } else {
      // Es un archivo File
      contenidoCSV = await archivoCSV.text();
    }

    // Parsear CSV
    const lineas = contenidoCSV.trim().split('\n');

    if (lineas.length < 2) {
      throw new Error('El archivo CSV está vacío o solo tiene encabezados');
    }

    const headers = lineas[0].split(',').map((h) => h.trim());
    console.log('Encabezados CSV:', headers);

    const registros: AforoCSVRecord[] = [];

    for (let i = 1; i < lineas.length; i++) {
      const linea = lineas[i].trim();
      if (!linea) continue; // Saltar líneas vacías

      const valores = linea.split(',').map((v) => v.trim());
      const registro: any = {};

      headers.forEach((header, index) => {
        const valor = valores[index];

        if (header === 'conteo' || header === 'movimiento_rilsa') {
          registro[header] = parseInt(valor, 10) || 0;
        } else {
          registro[header] = valor;
        }
      });

      registros.push(registro as AforoCSVRecord);
    }

    console.log('Total de registros parseados:', registros.length);
    console.log('Primer registro:', registros[0]);

    return procesarDatosAforoPorMovimiento(registros, metadata);
  } catch (error) {
    console.error('Error en cargarYProcesarCSV:', error);
    throw error;
  }
}
