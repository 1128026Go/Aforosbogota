/**
 * Utilidades para validar conteos de aforo
 * Asegura que los datos procesados coinciden con los CSV originales
 */

import type { DatosAforoPorMovimiento, AforoCSVRecord } from '@/types/aforo';

/**
 * Resultado de la validación
 */
export interface ResultadoValidacion {
  valido: boolean;
  errores: string[];
  advertencias: string[];
  estadisticas: {
    totalRegistrosCSV: number;
    totalVehiculosProcesados: number;
    totalPeatonesExcluidos: number;
    movimientosDetectados: number;
    intervalosDe15Min: number;
  };
}

/**
 * Valida que los conteos procesados coincidan con los registros CSV originales
 */
export function validarConteos(
  registrosCSV: AforoCSVRecord[],
  datosProcesados: DatosAforoPorMovimiento
): ResultadoValidacion {
  const errores: string[] = [];
  const advertencias: string[] = [];

  // 1. Validar que no haya registros vacíos
  if (registrosCSV.length === 0) {
    errores.push('El CSV no contiene registros');
    return {
      valido: false,
      errores,
      advertencias,
      estadisticas: {
        totalRegistrosCSV: 0,
        totalVehiculosProcesados: 0,
        totalPeatonesExcluidos: 0,
        movimientosDetectados: 0,
        intervalosDe15Min: 0,
      },
    };
  }

  // 2. Calcular totales desde CSV (excluyendo peatones)
  const totalesCSV = {
    autos: 0,
    buses: 0,
    camiones: 0,
    motos: 0,
    bicicletas: 0,
  };

  let totalPeatones = 0;

  registrosCSV.forEach((registro) => {
    switch (registro.clase) {
      case 'car':
        totalesCSV.autos += registro.conteo;
        break;
      case 'bus':
        totalesCSV.buses += registro.conteo;
        break;
      case 'truck':
        totalesCSV.camiones += registro.conteo;
        break;
      case 'motorcycle':
        totalesCSV.motos += registro.conteo;
        break;
      case 'bicycle':
        totalesCSV.bicicletas += registro.conteo;
        break;
      case 'person':
        totalPeatones += registro.conteo;
        break;
    }
  });

  // 3. Comparar con totales procesados
  const totalesProcesados = datosProcesados.volumenes_totales.totales;

  if (totalesCSV.autos !== totalesProcesados.autos) {
    errores.push(
      `Discrepancia en Autos: CSV=${totalesCSV.autos}, Procesados=${totalesProcesados.autos}`
    );
  }

  if (totalesCSV.buses !== totalesProcesados.buses) {
    errores.push(
      `Discrepancia en Buses: CSV=${totalesCSV.buses}, Procesados=${totalesProcesados.buses}`
    );
  }

  if (totalesCSV.camiones !== totalesProcesados.camiones) {
    errores.push(
      `Discrepancia en Camiones: CSV=${totalesCSV.camiones}, Procesados=${totalesProcesados.camiones}`
    );
  }

  if (totalesCSV.motos !== totalesProcesados.motos) {
    errores.push(
      `Discrepancia en Motos: CSV=${totalesCSV.motos}, Procesados=${totalesProcesados.motos}`
    );
  }

  if (totalesCSV.bicicletas !== totalesProcesados.bicicletas) {
    errores.push(
      `Discrepancia en Bicicletas: CSV=${totalesCSV.bicicletas}, Procesados=${totalesProcesados.bicicletas}`
    );
  }

  // 4. Validar que la suma de movimientos = totales
  const sumaPorMovimientos = {
    autos: 0,
    buses: 0,
    camiones: 0,
    motos: 0,
    bicicletas: 0,
  };

  Object.values(datosProcesados.movimientos).forEach((movimiento) => {
    sumaPorMovimientos.autos += movimiento.totales.autos;
    sumaPorMovimientos.buses += movimiento.totales.buses;
    sumaPorMovimientos.camiones += movimiento.totales.camiones;
    sumaPorMovimientos.motos += movimiento.totales.motos;
    sumaPorMovimientos.bicicletas += movimiento.totales.bicicletas;
  });

  if (sumaPorMovimientos.autos !== totalesProcesados.autos) {
    errores.push(
      `La suma de Autos por movimientos (${sumaPorMovimientos.autos}) no coincide con el total (${totalesProcesados.autos})`
    );
  }

  if (sumaPorMovimientos.buses !== totalesProcesados.buses) {
    errores.push(
      `La suma de Buses por movimientos (${sumaPorMovimientos.buses}) no coincide con el total (${totalesProcesados.buses})`
    );
  }

  if (sumaPorMovimientos.camiones !== totalesProcesados.camiones) {
    errores.push(
      `La suma de Camiones por movimientos (${sumaPorMovimientos.camiones}) no coincide con el total (${totalesProcesados.camiones})`
    );
  }

  if (sumaPorMovimientos.motos !== totalesProcesados.motos) {
    errores.push(
      `La suma de Motos por movimientos (${sumaPorMovimientos.motos}) no coincide con el total (${totalesProcesados.motos})`
    );
  }

  if (sumaPorMovimientos.bicicletas !== totalesProcesados.bicicletas) {
    errores.push(
      `La suma de Bicicletas por movimientos (${sumaPorMovimientos.bicicletas}) no coincide con el total (${totalesProcesados.bicicletas})`
    );
  }

  // 5. Advertencias
  if (totalPeatones > 0) {
    advertencias.push(
      `Se excluyeron ${totalPeatones} peatones de las tablas vehiculares (esto es esperado)`
    );
  }

  const movimientosDetectados = Object.keys(datosProcesados.movimientos).length;
  if (movimientosDetectados === 0) {
    advertencias.push('No se detectaron movimientos con datos');
  }

  if (movimientosDetectados > 10) {
    advertencias.push(
      `Se detectaron ${movimientosDetectados} movimientos, esperado máximo 10 según RILSA`
    );
  }

  // 6. Calcular estadísticas
  const totalVehiculosProcesados =
    totalesProcesados.autos +
    totalesProcesados.buses +
    totalesProcesados.camiones +
    totalesProcesados.motos +
    totalesProcesados.bicicletas;

  const estadisticas = {
    totalRegistrosCSV: registrosCSV.length,
    totalVehiculosProcesados,
    totalPeatonesExcluidos: totalPeatones,
    movimientosDetectados,
    intervalosDe15Min: datosProcesados.volumenes_totales.filas.length,
  };

  return {
    valido: errores.length === 0,
    errores,
    advertencias,
    estadisticas,
  };
}

/**
 * Imprime el resultado de validación de manera legible
 */
export function imprimirResultadoValidacion(resultado: ResultadoValidacion): void {
  console.group('🔍 Validación de Conteos de Aforo');

  if (resultado.valido) {
    console.log('✅ Validación exitosa - Los conteos son correctos');
  } else {
    console.log('❌ Validación fallida - Se encontraron errores');
  }

  console.group('📊 Estadísticas');
  console.table(resultado.estadisticas);
  console.groupEnd();

  if (resultado.errores.length > 0) {
    console.group('❌ Errores');
    resultado.errores.forEach((error) => console.error(error));
    console.groupEnd();
  }

  if (resultado.advertencias.length > 0) {
    console.group('⚠️ Advertencias');
    resultado.advertencias.forEach((advertencia) => console.warn(advertencia));
    console.groupEnd();
  }

  console.groupEnd();
}

/**
 * Valida y muestra resultados en consola
 */
export function validarYMostrar(
  registrosCSV: AforoCSVRecord[],
  datosProcesados: DatosAforoPorMovimiento
): boolean {
  const resultado = validarConteos(registrosCSV, datosProcesados);
  imprimirResultadoValidacion(resultado);
  return resultado.valido;
}
