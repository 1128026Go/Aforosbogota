/**
 * Utilidades para exportar datos de aforo a CSV
 */

import type { FilaVolumen, ConteosPorCategoria } from '@/types/aforo';

/**
 * Convierte datos a formato CSV y desencadena la descarga
 */
export function exportarTablaACSV(
  nombreBase: string,
  filas: FilaVolumen[],
  totales: ConteosPorCategoria,
  metadata?: {
    ubicacion?: string;
    fecha?: string;
    fecha_iso?: string;
  }
): void {
  // Construir contenido CSV
  const lineas: string[] = [];

  // Agregar metadatos como comentarios (opcional)
  if (metadata) {
    lineas.push(`# Ubicación: ${metadata.ubicacion || 'N/A'}`);
    lineas.push(`# Fecha: ${metadata.fecha || metadata.fecha_iso || 'N/A'}`);
    lineas.push('');
  }

  // Encabezados
  lineas.push('Periodo,Autos,Buses,Camiones,Motos,Bicicletas');

  // Filas de datos
  filas.forEach((fila) => {
    lineas.push(
      `${fila.periodo},${fila.autos},${fila.buses},${fila.camiones},${fila.motos},${fila.bicicletas}`
    );
  });

  // Fila de totales
  lineas.push(
    `TOTAL,${totales.autos},${totales.buses},${totales.camiones},${totales.motos},${totales.bicicletas}`
  );

  // Unir todas las líneas
  const contenidoCSV = lineas.join('\n');

  // Crear blob y desencadenar descarga
  const blob = new Blob([contenidoCSV], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);

  // Crear elemento de descarga temporal
  const link = document.createElement('a');
  link.href = url;

  // Construir nombre de archivo
  const fechaStr = metadata?.fecha_iso?.replace(/-/g, '') || new Date().toISOString().split('T')[0].replace(/-/g, '');
  const nombreArchivo = `${nombreBase}_${fechaStr}.csv`;

  link.download = nombreArchivo;
  link.style.display = 'none';

  // Agregar al DOM, hacer clic y remover
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Liberar URL del blob
  URL.revokeObjectURL(url);
}

/**
 * Exporta todos los movimientos a un archivo ZIP (requiere biblioteca adicional)
 * Por ahora, solo descarga cada uno por separado
 */
export async function exportarTodosLosMovimientos(
  datos: any, // DatosAforoPorMovimiento
  opciones?: {
    incluirTotales?: boolean;
  }
): Promise<void> {
  const { incluirTotales = true } = opciones || {};

  // Exportar volúmenes totales
  if (incluirTotales && datos.volumenes_totales) {
    exportarTablaACSV(
      'Volumenes_Totales',
      datos.volumenes_totales.filas,
      datos.volumenes_totales.totales,
      datos.metadata
    );

    // Pequeña pausa para evitar que los navegadores bloqueen múltiples descargas
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  // Exportar cada movimiento
  const movimientos = Object.values(datos.movimientos || {}) as any[];

  for (const movimiento of movimientos) {
    exportarTablaACSV(
      `Mov${movimiento.codigo}_${movimiento.nombre.replace(/\s*→\s*/g, '-')}`,
      movimiento.filas,
      movimiento.totales,
      datos.metadata
    );

    // Pausa entre descargas
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

/**
 * Copia el contenido CSV al portapapeles
 */
export async function copiarCSVAlPortapapeles(
  filas: FilaVolumen[],
  totales: ConteosPorCategoria
): Promise<boolean> {
  try {
    const lineas: string[] = [];

    // Encabezados
    lineas.push('Periodo\tAutos\tBuses\tCamiones\tMotos\tBicicletas');

    // Filas de datos (usar tab como separador para mejor compatibilidad con Excel)
    filas.forEach((fila) => {
      lineas.push(
        `${fila.periodo}\t${fila.autos}\t${fila.buses}\t${fila.camiones}\t${fila.motos}\t${fila.bicicletas}`
      );
    });

    // Fila de totales
    lineas.push(
      `TOTAL\t${totales.autos}\t${totales.buses}\t${totales.camiones}\t${totales.motos}\t${totales.bicicletas}`
    );

    const contenido = lineas.join('\n');

    await navigator.clipboard.writeText(contenido);
    return true;
  } catch (error) {
    console.error('Error al copiar al portapapeles:', error);
    return false;
  }
}
