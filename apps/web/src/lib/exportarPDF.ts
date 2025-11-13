/**
 * Utilidad para exportar análisis completo de intersección a PDF
 * Incluye tablas, gráficos y mapas
 */

import { API_BASE_URL } from '@/config/api';
import { type DatosAforoPorMovimiento } from '@/types/aforo';
import { createCardinalZonesDebugCanvas } from './debugCardinalZones';
import {
  obtenerDescripcionMovimiento,
  obtenerNombreMovimiento,
} from './movimientos';

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
  hide_in_pdf?: boolean;
}

interface CardinalAccess {
  id: string;
  display_name: string;
  cardinal_official: string;
  gate: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
}

interface ExportPDFOptions {
  datos: DatosAforoPorMovimiento;
  graficos: {
    heatmapCanvas?: HTMLCanvasElement;
    conflictsCanvas?: HTMLCanvasElement;
    trajectoryCanvas?: HTMLCanvasElement;
    speedsElement?: HTMLElement;
    modesElement?: HTMLElement;
    odMatrixElement?: HTMLElement;
    evolutionElement?: HTMLElement;
    volumeDiagramElement?: HTMLElement;
  };
  playbackEvents?: PlaybackEvent[];
  cardinals?: CardinalAccess[];
  metadata?: {
    proyecto?: string;
    responsable?: string;
    notas?: string;
  };
  datasetId?: string;
}

/**
 * Exportar análisis completo a PDF usando jsPDF
 *
 * NOTA: Requiere instalar: npm install jspdf html2canvas
 */
export async function exportarAnalisisCompletoPDF(options: ExportPDFOptions): Promise<void> {
  const { datos, graficos, metadata = {}, datasetId } = options;
  let playbackEvents = options.playbackEvents ?? [];
  let cardinals = options.cardinals ?? [];

  try {
    if (datasetId) {
      if (playbackEvents.length === 0) {
        const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/playback-events`);
        if (res.ok) {
          const data = await res.json();
          playbackEvents = Array.isArray(data.events) ? data.events : [];
        }
      }

      if (cardinals.length === 0) {
        const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/cardinals`);
        if (res.ok) {
          const data = await res.json();
          cardinals = Array.isArray(data.accesses) ? data.accesses : [];
        }
      }
    }
  } catch (error) {
    console.warn('No se pudieron cargar datos adicionales para el PDF:', error);
  }

  // Filtrar eventos ocultos o descartados
  playbackEvents = playbackEvents.filter((event) => !event.hide_in_pdf);

  // Verificar si jsPDF está disponible
  if (typeof window === 'undefined') {
    throw new Error('Esta función solo funciona en el navegador');
  }

  try {
    // Importación dinámica de jsPDF y html2canvas
    const { jsPDF } = await import('jspdf');
    const html2canvas = (await import('html2canvas')).default;

    // Crear documento PDF (A4, portrait)
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 20; // Aumentado para mejor legibilidad
    const contentWidth = pageWidth - 2 * margin;
    let currentY = margin;

    // Función auxiliar para dibujar tabla con bordes y zebra striping
    const drawTable = (headers: string[], rows: string[][], startY: number, includeTotal?: string[]) => {
      const colWidth = contentWidth / headers.length;
      let yPos = startY;

      // Dibujar borde exterior de tabla
      const rowHeight = 5;
      const headerHeight = 7;
      const totalHeight = 6;
      const tableHeight = rows.length * rowHeight + headerHeight + (includeTotal ? totalHeight : 0);
      doc.setDrawColor(200, 200, 200);
      doc.setLineWidth(0.5);
      doc.rect(margin, yPos, contentWidth, tableHeight);

      // Encabezados con fondo gris más oscuro
      doc.setFillColor(220, 220, 220);
      doc.rect(margin, yPos, contentWidth, headerHeight, 'F');

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(0, 0, 0);

      let xPos = margin;
      headers.forEach((header, i) => {
        // Líneas verticales entre columnas
        if (i > 0) {
          doc.line(xPos, yPos, xPos, yPos + tableHeight);
        }
        doc.text(header, xPos + colWidth / 2, yPos + 4.5, { align: 'center' });
        xPos += colWidth;
      });

      yPos += headerHeight;

      // Línea horizontal después del encabezado
      doc.line(margin, yPos, margin + contentWidth, yPos);

      // Filas de datos con zebra striping
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7);

      rows.forEach((row, index) => {
        // Zebra striping - filas impares con fondo gris claro
        if (index % 2 === 1) {
          doc.setFillColor(245, 245, 245);
          doc.rect(margin, yPos, contentWidth, rowHeight, 'F');
        }

        xPos = margin;
        row.forEach((cell, i) => {
          // Líneas verticales
          if (i > 0) {
            doc.line(xPos, yPos, xPos, yPos + rowHeight);
          }

          // Centrar números, alinear izquierda texto
          const align = i === 0 ? 'left' : 'center';
          const xOffset = i === 0 ? 2 : colWidth / 2;
          doc.text(cell, xPos + xOffset, yPos + 3.5, { align });
          xPos += colWidth;
        });

        yPos += rowHeight;
        // Línea horizontal entre filas
        doc.setDrawColor(230, 230, 230);
        doc.line(margin, yPos, margin + contentWidth, yPos);
      });

      // Fila de totales si existe
      if (includeTotal) {
        doc.setFillColor(230, 240, 255); // Azul claro para totales
        doc.rect(margin, yPos, contentWidth, totalHeight, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);

        xPos = margin;
        includeTotal.forEach((cell, i) => {
          if (i > 0) {
            doc.line(xPos, yPos, xPos, yPos + totalHeight);
          }
          const align = i === 0 ? 'left' : 'center';
          const xOffset = i === 0 ? 2 : colWidth / 2;
          doc.text(cell, xPos + xOffset, yPos + 4, { align });
          xPos += colWidth;
        });
        yPos += totalHeight;
      }

      // Borde inferior de tabla
      doc.setDrawColor(200, 200, 200);
      doc.setLineWidth(0.5);
      doc.line(margin, yPos, margin + contentWidth, yPos);

      return yPos;
    };

    // Función para agregar numeración de páginas al final
    const addPageNumbers = () => {
      const pageCount = doc.getNumberOfPages();
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.setTextColor(100, 100, 100);

      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.text(
          `Página ${i} de ${pageCount}`,
          pageWidth / 2,
          pageHeight - 10,
          { align: 'center' }
        );
      }
    };

    // ========== PORTADA ==========
    doc.setFillColor(102, 126, 234); // #667eea
    doc.rect(0, 0, pageWidth, 60, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(24);
    doc.setFont('helvetica', 'bold');
    doc.text('ANALISIS DE INTERSECCION', pageWidth / 2, 25, { align: 'center' });

    doc.setFontSize(14);
    doc.setFont('helvetica', 'normal');
    doc.text('Aforo Vehicular y Estudio de Trafico', pageWidth / 2, 35, { align: 'center' });

    currentY = 75;

    // Información general
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');

    const addInfoLine = (label: string, value: string) => {
      doc.setFont('helvetica', 'bold');
      doc.text(label + ':', margin, currentY);
      doc.setFont('helvetica', 'normal');
      doc.text(value, margin + 40, currentY);
      currentY += 8;
    };

    addInfoLine('Ubicacion', datos.metadata.ubicacion);
    addInfoLine('Fecha', datos.metadata.fecha);
    addInfoLine('Periodo', `${datos.metadata.hora_inicio} - ${datos.metadata.hora_fin}`);

    if (metadata.proyecto) {
      addInfoLine('Proyecto', metadata.proyecto);
    }
    if (metadata.responsable) {
      addInfoLine('Responsable', metadata.responsable);
    }

    currentY += 10;

    // Resumen ejecutivo
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('RESUMEN EJECUTIVO', margin, currentY);
    currentY += 8;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');

    const totalVehiculos = datos.volumenes_totales.totales.autos +
                          datos.volumenes_totales.totales.buses +
                          datos.volumenes_totales.totales.camiones +
                          datos.volumenes_totales.totales.motos +
                          datos.volumenes_totales.totales.bicicletas +
                          datos.volumenes_totales.totales.peatones;

    const numMovimientos = Object.keys(datos.movimientos).length;

    const resumenText = [
      `- Total de vehiculos contados: ${totalVehiculos.toLocaleString()}`,
      `- Numero de movimientos detectados: ${numMovimientos}`,
      `- Autos: ${datos.volumenes_totales.totales.autos.toLocaleString()} (${((datos.volumenes_totales.totales.autos / totalVehiculos) * 100).toFixed(1)}%)`,
      `- Buses: ${datos.volumenes_totales.totales.buses.toLocaleString()} (${((datos.volumenes_totales.totales.buses / totalVehiculos) * 100).toFixed(1)}%)`,
      `- Camiones: ${datos.volumenes_totales.totales.camiones.toLocaleString()} (${((datos.volumenes_totales.totales.camiones / totalVehiculos) * 100).toFixed(1)}%)`,
      `- Motos: ${datos.volumenes_totales.totales.motos.toLocaleString()} (${((datos.volumenes_totales.totales.motos / totalVehiculos) * 100).toFixed(1)}%)`,
      `- Bicicletas: ${datos.volumenes_totales.totales.bicicletas.toLocaleString()} (${((datos.volumenes_totales.totales.bicicletas / totalVehiculos) * 100).toFixed(1)}%)`,
      `- Peatones: ${datos.volumenes_totales.totales.peatones.toLocaleString()} (${((datos.volumenes_totales.totales.peatones / totalVehiculos) * 100).toFixed(1)}%)`,
    ];

    resumenText.forEach(line => {
      doc.text(line, margin + 5, currentY);
      currentY += 6;
    });

    currentY += 10;

    // Gráfico de pastel de composición vehicular
    const graficoPastel = crearGraficoPastel(datos.volumenes_totales.totales);
    const pastelWidth = contentWidth * 0.9;
    const pastelHeight = (500 / 800) * pastelWidth; // Mantener proporción
    doc.addImage(graficoPastel, 'PNG', margin + contentWidth * 0.05, currentY, pastelWidth, pastelHeight);

    // ========== PAGINA DE DEBUG: ZONAS CARDINALES ==========
    console.log('🔍 DEBUG PDF - Verificando datos para página de debug:');
    console.log('  - playbackEvents:', playbackEvents.length);
    console.log('  - cardinals:', cardinals.length);

    if (playbackEvents.length > 0 && cardinals.length > 0) {
      console.log('✅ Generando página de debug de zonas cardinales...');

      doc.addPage();
      currentY = margin;

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(0, 0, 0);
      doc.text('DEBUG: Zonas de Acceso Cardinal', margin, currentY);
      currentY += 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('Visualizacion de las zonas configuradas para detectar movimientos', margin, currentY);
      currentY += 5;
      doc.text('Lineas de colores = Gates de acceso | Puntos verdes = Inicio | Puntos rojos = Fin', margin, currentY);
      currentY += 10;

      try {
        const debugCanvas = createCardinalZonesDebugCanvas(playbackEvents, cardinals);
        const debugWidth = contentWidth;
        const debugHeight = (800 / 1400) * debugWidth;

        doc.addImage(debugCanvas, 'PNG', margin, currentY, debugWidth, debugHeight);
        console.log('✅ Página de debug agregada correctamente');
      } catch (error) {
        console.error('❌ Error generando canvas de debug:', error);
      }
    } else {
      console.log('❌ No se generará página de debug - Falta información');
    }

    // ========== NUEVA PAGINA: VOLUMENES TOTALES ==========
    doc.addPage();
    currentY = margin;

    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text('1. VOLUMENES TOTALES', margin, currentY);
    currentY += 10;

    // Tabla de volúmenes totales usando función mejorada
    const { filas, totales } = datos.volumenes_totales;
    const headers = ['Periodo', 'Autos', 'Buses', 'Camiones', 'Motos', 'Bicicletas', 'Peatones'];

    const filasData = filas.map(fila => [
      fila.periodo,
      fila.autos.toString(),
      fila.buses.toString(),
      fila.camiones.toString(),
      fila.motos.toString(),
      fila.bicicletas.toString(),
      fila.peatones.toString(),
    ]);

    const totalesRow = [
      'TOTAL',
      totales.autos.toString(),
      totales.buses.toString(),
      totales.camiones.toString(),
      totales.motos.toString(),
      totales.bicicletas.toString(),
      totales.peatones.toString(),
    ];

    currentY = drawTable(headers, filasData, currentY, totalesRow);
    currentY += 15;

    // Gráfico de lineas para volúmenes totales
    doc.addPage();
    currentY = margin;

    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Evolucion Temporal de Volumenes Totales', margin, currentY);
    currentY += 10;

    const graficoBarrasTotales = crearGraficoBarrasTemporal(
      filas,
      'Evolucion Vehicular por Tipo - Intervalo de 15 Minutos'
    );
    const barrasTotalesWidth = contentWidth;
    const barrasTotalesHeight = (400 / 1200) * barrasTotalesWidth;

    doc.addImage(graficoBarrasTotales, 'PNG', margin, currentY, barrasTotalesWidth, barrasTotalesHeight);
    currentY += barrasTotalesHeight + 15;

    // Gráfico de Evolución Temporal (si existe)
    if (graficos.evolutionElement) {
      if (currentY > pageHeight - 100) {
        doc.addPage();
        currentY = margin;
      }

      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('Evolución Temporal de Volúmenes', margin, currentY);
      currentY += 8;

      const evolutionCanvas = await html2canvas(graficos.evolutionElement, {
        scale: 2,
        backgroundColor: '#ffffff'
      });

      const evolutionImg = evolutionCanvas.toDataURL('image/png');
      const imgWidth = contentWidth;
      const imgHeight = (evolutionCanvas.height / evolutionCanvas.width) * imgWidth;

      doc.addImage(evolutionImg, 'PNG', margin, currentY, imgWidth, Math.min(imgHeight, 100));
      currentY += Math.min(imgHeight, 100) + 10;
    }

    // Diagrama de Volúmenes (si existe)
    if (graficos.volumeDiagramElement) {
      if (currentY > pageHeight - 100) {
        doc.addPage();
        currentY = margin;
      }

      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('Diagrama de Flujos por Movimiento', margin, currentY);
      currentY += 8;

      const diagramCanvas = await html2canvas(graficos.volumeDiagramElement, {
        scale: 2,
        backgroundColor: '#ffffff'
      });

      const diagramImg = diagramCanvas.toDataURL('image/png');
      const imgWidth = contentWidth;
      const imgHeight = (diagramCanvas.height / diagramCanvas.width) * imgWidth;

      doc.addImage(diagramImg, 'PNG', margin, currentY, imgWidth, Math.min(imgHeight, 110));
      currentY += Math.min(imgHeight, 110) + 10;
    }

    // ========== GRÁFICOS ADICIONALES ==========

    // Mapa de calor
    if (graficos.heatmapCanvas) {
      doc.addPage();
      currentY = margin;

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('2. MAPA DE CALOR DE TRAYECTORIAS', margin, currentY);
      currentY += 10;

      const heatmapImg = graficos.heatmapCanvas.toDataURL('image/png');
      const imgWidth = contentWidth;
      const imgHeight = (graficos.heatmapCanvas.height / graficos.heatmapCanvas.width) * imgWidth;

      doc.addImage(heatmapImg, 'PNG', margin, currentY, imgWidth, Math.min(imgHeight, 150));
      currentY += Math.min(imgHeight, 150) + 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('Densidad de trayectorias vehiculares en la intersección', margin, currentY);
    }

    // Zonas de conflicto
    if (graficos.conflictsCanvas) {
      doc.addPage();
      currentY = margin;

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('3. ZONAS DE CONFLICTO', margin, currentY);
      currentY += 10;

      const conflictsImg = graficos.conflictsCanvas.toDataURL('image/png');
      const imgWidth = contentWidth;
      const imgHeight = (graficos.conflictsCanvas.height / graficos.conflictsCanvas.width) * imgWidth;

      doc.addImage(conflictsImg, 'PNG', margin, currentY, imgWidth, Math.min(imgHeight, 150));
      currentY += Math.min(imgHeight, 150) + 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('Puntos de cruce y potenciales conflictos entre trayectorias', margin, currentY);
    }

    // Canvas de trayectorias
    if (graficos.trajectoryCanvas) {
      doc.addPage();
      currentY = margin;

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('4. TRAYECTORIAS INDIVIDUALES', margin, currentY);
      currentY += 10;

      const trajImg = graficos.trajectoryCanvas.toDataURL('image/png');
      const imgWidth = contentWidth;
      const imgHeight = (graficos.trajectoryCanvas.height / graficos.trajectoryCanvas.width) * imgWidth;

      doc.addImage(trajImg, 'PNG', margin, currentY, imgWidth, Math.min(imgHeight, 150));
      currentY += Math.min(imgHeight, 150) + 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('Visualización de trayectorias individuales por clase vehicular', margin, currentY);
    }

    // Gráfico de velocidades
    if (graficos.speedsElement) {
      doc.addPage();
      currentY = margin;

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('5. ANÁLISIS DE VELOCIDADES', margin, currentY);
      currentY += 10;

      const speedsCanvas = await html2canvas(graficos.speedsElement, {
        scale: 2,
        backgroundColor: '#ffffff'
      });

      const speedsImg = speedsCanvas.toDataURL('image/png');
      const imgWidth = contentWidth;
      const imgHeight = (speedsCanvas.height / speedsCanvas.width) * imgWidth;

      doc.addImage(speedsImg, 'PNG', margin, currentY, imgWidth, Math.min(imgHeight, 120));
      currentY += Math.min(imgHeight, 120) + 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('Distribución de velocidades por movimiento RILSA', margin, currentY);
    }

    // Composición vehicular (Modes)
    if (graficos.modesElement) {
      doc.addPage();
      currentY = margin;

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('6. COMPOSICIÓN VEHICULAR', margin, currentY);
      currentY += 10;

      const modesCanvas = await html2canvas(graficos.modesElement, {
        scale: 2,
        backgroundColor: '#ffffff'
      });

      const modesImg = modesCanvas.toDataURL('image/png');
      const imgWidth = contentWidth;
      const imgHeight = (modesCanvas.height / modesCanvas.width) * imgWidth;

      doc.addImage(modesImg, 'PNG', margin, currentY, imgWidth, Math.min(imgHeight, 120));
      currentY += Math.min(imgHeight, 120) + 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('Distribución porcentual de tipos de vehículos', margin, currentY);
    }

    // Matriz Origen-Destino
    if (graficos.odMatrixElement) {
      doc.addPage();
      currentY = margin;

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('7. MATRIZ ORIGEN-DESTINO', margin, currentY);
      currentY += 10;

      const odCanvas = await html2canvas(graficos.odMatrixElement, {
        scale: 2,
        backgroundColor: '#ffffff'
      });

      const odImg = odCanvas.toDataURL('image/png');
      const imgWidth = contentWidth;
      const imgHeight = (odCanvas.height / odCanvas.width) * imgWidth;

      doc.addImage(odImg, 'PNG', margin, currentY, imgWidth, Math.min(imgHeight, 120));
      currentY += Math.min(imgHeight, 120) + 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('Flujos vehiculares entre accesos de la intersección', margin, currentY);
    }

    // ========== MOVIMIENTOS INDIVIDUALES ==========
    const movimientosOrdenados = Object.values(datos.movimientos).sort((a, b) => a.codigo - b.codigo);

    movimientosOrdenados.forEach((mov, index) => {
      doc.addPage();
      currentY = margin;

      // Usar nombre descriptivo correcto del movimiento
      // Para retornos (101-104), origen y destino son iguales
      const nombreSimple = obtenerNombreMovimiento({
        codigo: mov.codigo,
        nombre: mov.nombre,
        origen: mov.origen,
        destino: mov.destino,
      });
      const descripcionCorta = obtenerDescripcionMovimiento(mov.tipo);
      const tituloMovimiento = descripcionCorta
        ? `${8 + index}. MOVIMIENTO ${mov.codigo}: ${nombreSimple} (${descripcionCorta})`
        : `${8 + index}. MOVIMIENTO ${mov.codigo}: ${nombreSimple}`;

      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(0, 0, 0);
      doc.text(tituloMovimiento, margin, currentY);
      currentY += 7;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(80, 80, 80);
      const tipoSimple = mov.tipo.replace('_', ' ').toUpperCase();
      doc.text(`Tipo: ${tipoSimple}`, margin, currentY);
      currentY += 8;

      // Tabla del movimiento (primero, más compacta)
      const filasMovimiento = mov.filas.map(fila => [
        fila.periodo,
        fila.autos.toString(),
        fila.buses.toString(),
        fila.camiones.toString(),
        fila.motos.toString(),
        fila.bicicletas.toString(),
        fila.peatones.toString(),
      ]);

      const totalesMovimiento = [
        'TOTAL',
        mov.totales.autos.toString(),
        mov.totales.buses.toString(),
        mov.totales.camiones.toString(),
        mov.totales.motos.toString(),
        mov.totales.bicicletas.toString(),
        mov.totales.peatones.toString(),
      ];

      currentY = drawTable(headers, filasMovimiento, currentY, totalesMovimiento);
      currentY += 8;

      // Canvas de trayectorias filtrado por movimiento (si hay eventos disponibles)
      if (playbackEvents.length > 0) {
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(0, 0, 0);
        const tituloTrayectorias = descripcionCorta
          ? `Trayectorias - Movimiento ${mov.codigo}: ${nombreSimple} (${descripcionCorta})`
          : `Trayectorias - Movimiento ${mov.codigo}: ${nombreSimple}`;
        doc.text(tituloTrayectorias, margin, currentY);
        currentY += 5;

        const canvasTrayectorias = crearCanvasTrayectoriasFiltrado(
          playbackEvents,
          mov.codigo,
          nombreSimple,
          descripcionCorta
        );
        const trajWidth = contentWidth;
        const trajHeight = (400 / 1000) * trajWidth;

        doc.addImage(canvasTrayectorias, 'PNG', margin, currentY, trajWidth, trajHeight);
      }
    });

    // ========== FOOTER EN ULTIMA PAGINA ==========
    doc.addPage();
    currentY = pageHeight - 40;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(127, 140, 141);
    doc.text(`Generado el ${new Date().toLocaleString('es-CO')}`, pageWidth / 2, currentY, { align: 'center' });
    doc.text('Sistema de Aforo RILSA - Analisis de Trafico', pageWidth / 2, currentY + 6, { align: 'center' });

    if (metadata.notas) {
      currentY += 15;
      doc.setFontSize(8);
      doc.text(`Notas: ${metadata.notas}`, margin, currentY);
    }

    // ========== AGREGAR NUMERACION DE PAGINAS ==========
    addPageNumbers();

    // ========== GUARDAR PDF ==========
    const filename = `Analisis_Interseccion_${datos.metadata.fecha_iso}_${datos.metadata.hora_inicio.replace(':', '')}.pdf`;
    doc.save(filename);

    console.log('PDF generado: ' + filename);

  } catch (error) {
    console.error('Error generando PDF:', error);
    throw new Error(`Error al generar PDF: ${error instanceof Error ? error.message : 'Error desconocido'}`);
  }
}

/**
 * Función auxiliar para capturar un elemento HTML como imagen
 */
async function capturarElementoComoImagen(element: HTMLElement): Promise<string> {
  const html2canvas = (await import('html2canvas')).default;
  const canvas = await html2canvas(element, {
    scale: 2,
    backgroundColor: '#ffffff',
    logging: false,
  });
  return canvas.toDataURL('image/png');
}

/**
 * Crear gráfico de pastel para composición vehicular
 */
function crearGraficoPastel(totales: {
  autos: number;
  buses: number;
  camiones: number;
  motos: number;
  bicicletas: number;
  peatones: number;
}): string {
  const canvas = document.createElement('canvas');
  canvas.width = 800;
  canvas.height = 500;
  const ctx = canvas.getContext('2d')!;

  // Fondo blanco
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Datos
  const categorias = [
    { nombre: 'Autos', valor: totales.autos, color: '#3b82f6' },
    { nombre: 'Buses', valor: totales.buses, color: '#10b981' },
    { nombre: 'Camiones', valor: totales.camiones, color: '#f59e0b' },
    { nombre: 'Motos', valor: totales.motos, color: '#8b5cf6' },
    { nombre: 'Bicicletas', valor: totales.bicicletas, color: '#06b6d4' },
    { nombre: 'Peatones', valor: totales.peatones, color: '#ec4899' },
  ].filter(cat => cat.valor > 0);

  const total = categorias.reduce((sum, cat) => sum + cat.valor, 0);

  // Titulo
  ctx.fillStyle = '#000000';
  ctx.font = 'bold 24px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('COMPOSICION VEHICULAR GENERAL', canvas.width / 2, 35);

  // Dibujar pastel
  const centerX = 280;
  const centerY = 260;
  const radius = 140;
  let currentAngle = -Math.PI / 2;

  categorias.forEach(cat => {
    const sliceAngle = (cat.valor / total) * 2 * Math.PI;

    // Dibujar slice
    ctx.fillStyle = cat.color;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
    ctx.closePath();
    ctx.fill();

    // Borde blanco
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Etiqueta de porcentaje
    const porcentaje = ((cat.valor / total) * 100).toFixed(1);
    if (parseFloat(porcentaje) > 5) {
      const labelAngle = currentAngle + sliceAngle / 2;
      const labelX = centerX + Math.cos(labelAngle) * (radius * 0.65);
      const labelY = centerY + Math.sin(labelAngle) * (radius * 0.65);

      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 18px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${porcentaje}%`, labelX, labelY);
    }

    currentAngle += sliceAngle;
  });

  // Leyenda
  const legendX = 480;
  let legendY = 100;

  categorias.forEach(cat => {
    // Cuadro de color
    ctx.fillStyle = cat.color;
    ctx.fillRect(legendX, legendY - 12, 30, 20);
    ctx.strokeStyle = '#cccccc';
    ctx.lineWidth = 1;
    ctx.strokeRect(legendX, legendY - 12, 30, 20);

    // Texto
    ctx.fillStyle = '#000000';
    ctx.font = '16px Arial';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(cat.nombre, legendX + 40, legendY);

    // Valor y porcentaje
    const porcentaje = ((cat.valor / total) * 100).toFixed(1);
    ctx.font = 'bold 16px Arial';
    ctx.fillText(`${cat.valor.toLocaleString()} (${porcentaje}%)`, legendX + 40, legendY + 18);

    legendY += 55;
  });

  return canvas.toDataURL('image/png');
}

/**
 * Crear gráfico de líneas múltiples para evolución temporal
 */
function crearGraficoBarrasTemporal(
  filas: Array<{
    periodo: string;
    autos: number;
    buses: number;
    camiones: number;
    motos: number;
    bicicletas: number;
    peatones: number;
  }>,
  titulo: string
): string {
  const canvas = document.createElement('canvas');
  canvas.width = 1200;
  canvas.height = 400;
  const ctx = canvas.getContext('2d')!;

  // Fondo blanco
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Titulo
  ctx.fillStyle = '#000000';
  ctx.font = 'bold 16px Arial';
  ctx.textAlign = 'center';
  ctx.fillText(titulo, canvas.width / 2, 25);

  // Area de grafico
  const chartLeft = 70;
  const chartTop = 60;
  const chartWidth = canvas.width - 240;
  const chartHeight = canvas.height - 110;

  // Encontrar valor máximo (suma apilada)
  const maxValor = Math.max(
    ...filas.map(f => f.autos + f.buses + f.camiones + f.motos + f.bicicletas + f.peatones)
  );

  // Escala Y
  const yScale = chartHeight / (maxValor * 1.1);

  // Categorías y colores
  const categorias = [
    { key: 'autos', nombre: 'Autos', color: '#3b82f6' },
    { key: 'buses', nombre: 'Buses', color: '#10b981' },
    { key: 'camiones', nombre: 'Camiones', color: '#f59e0b' },
    { key: 'motos', nombre: 'Motos', color: '#8b5cf6' },
    { key: 'bicicletas', nombre: 'Bicicletas', color: '#06b6d4' },
    { key: 'peatones', nombre: 'Peatones', color: '#ec4899' },
  ];

  // Dibujar ejes
  ctx.strokeStyle = '#cccccc';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(chartLeft, chartTop);
  ctx.lineTo(chartLeft, chartTop + chartHeight);
  ctx.lineTo(chartLeft + chartWidth, chartTop + chartHeight);
  ctx.stroke();

  // Etiquetas Y
  ctx.fillStyle = '#666666';
  ctx.font = '11px Arial';
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';

  for (let i = 0; i <= 5; i++) {
    const valor = (maxValor / 5) * i;
    const y = chartTop + chartHeight - (valor * yScale);

    ctx.strokeStyle = '#eeeeee';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(chartLeft, y);
    ctx.lineTo(chartLeft + chartWidth, y);
    ctx.stroke();

    ctx.fillText(Math.round(valor).toString(), chartLeft - 10, y);
  }

  // Dibujar barras apiladas
  const barWidth = chartWidth / filas.length * 0.7;
  const barSpacing = chartWidth / filas.length;

  filas.forEach((fila, index) => {
    const x = chartLeft + index * barSpacing + barSpacing * 0.15;
    let yOffset = 0;

    categorias.forEach(cat => {
      const valor = (fila as any)[cat.key];
      const barHeight = valor * yScale;

      ctx.fillStyle = cat.color;
      ctx.fillRect(
        x,
        chartTop + chartHeight - yOffset - barHeight,
        barWidth,
        barHeight
      );

      yOffset += barHeight;
    });
  });

  // Etiquetas X (cada 2 periodos)
  filas.forEach((fila, index) => {
    if (index % 2 === 0 || index === filas.length - 1) {
      ctx.fillStyle = '#666666';
      ctx.font = '9px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      const periodoSimple = fila.periodo.split('-')[0].trim();
      const x = chartLeft + index * barSpacing + barSpacing / 2;
      ctx.fillText(periodoSimple, x, chartTop + chartHeight + 5);
    }
  });

  // Leyenda compacta
  const legendX = canvas.width - 160;
  let legendY = chartTop + 15;

  ctx.fillStyle = '#000000';
  ctx.font = 'bold 12px Arial';
  ctx.textAlign = 'left';
  ctx.fillText('Leyenda:', legendX, legendY);
  legendY += 20;

  categorias.forEach(cat => {
    ctx.fillStyle = cat.color;
    ctx.fillRect(legendX, legendY - 7, 15, 12);
    ctx.strokeStyle = '#999999';
    ctx.lineWidth = 1;
    ctx.strokeRect(legendX, legendY - 7, 15, 12);

    ctx.fillStyle = '#000000';
    ctx.font = '10px Arial';
    ctx.fillText(cat.nombre, legendX + 20, legendY);

    legendY += 18;
  });

  return canvas.toDataURL('image/png');
}

/**
 * Crear canvas de trayectorias filtrado por movimiento
 */
function crearCanvasTrayectoriasFiltrado(
  eventos: PlaybackEvent[],
  codigoMovimiento: number,
  nombreMovimiento: string,
  descripcionMovimiento?: string
): string {
  const canvas = document.createElement('canvas');
  canvas.width = 1000;
  canvas.height = 400;
  const ctx = canvas.getContext('2d')!;

  // Filtrar eventos por movimiento
  const eventosFiltrados = eventos.filter(e => e.mov_rilsa === codigoMovimiento);

  if (eventosFiltrados.length === 0) {
    // Fondo negro con mensaje
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ffffff';
    ctx.font = '20px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('No hay trayectorias para este movimiento', canvas.width / 2, canvas.height / 2);
    return canvas.toDataURL('image/png');
  }

  // Fondo negro
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Calcular bounds
  const padding = 60;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

  eventosFiltrados.forEach(event => {
    event.positions.forEach(([x, y]) => {
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    });
  });

  const dataWidth = maxX - minX || 1;
  const dataHeight = maxY - minY || 1;
  const scaleX = (canvas.width - padding * 2) / dataWidth;
  const scaleY = (canvas.height - padding * 2) / dataHeight;
  const scale = Math.min(scaleX, scaleY);

  const offsetX = padding + (canvas.width - padding * 2 - dataWidth * scale) / 2;
  const offsetY = padding + (canvas.height - padding * 2 - dataHeight * scale) / 2;

  function transform(x: number, y: number): [number, number] {
    return [
      offsetX + (x - minX) * scale,
      offsetY + (y - minY) * scale,
    ];
  }

  // Colores por clase
  const CLASE_COLORS: Record<string, string> = {
    car: '#3b82f6',
    motorcycle: '#e74c3c',
    bus: '#f39c12',
    truck: '#9b59b6',
    bicycle: '#2ecc71',
    person: '#1abc9c',
  };

  // Dibujar trayectorias
  eventosFiltrados.forEach(event => {
    const color = CLASE_COLORS[event.class] || '#95a5a6';

    // Trayectoria completa
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.shadowBlur = 5;
    ctx.shadowColor = color;
    ctx.beginPath();

    event.positions.forEach(([px, py], i) => {
      const [x, y] = transform(px, py);
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();
    ctx.shadowBlur = 0;

    // Punto inicial (verde)
    if (event.positions.length > 0) {
      const [startX, startY] = transform(event.positions[0][0], event.positions[0][1]);
      ctx.fillStyle = '#00ff00';
      ctx.beginPath();
      ctx.arc(startX, startY, 5, 0, 2 * Math.PI);
      ctx.fill();
    }

    // Punto final (rojo)
    if (event.positions.length > 1) {
      const lastIdx = event.positions.length - 1;
      const [endX, endY] = transform(event.positions[lastIdx][0], event.positions[lastIdx][1]);
      ctx.fillStyle = '#ff0000';
      ctx.beginPath();
      ctx.arc(endX, endY, 5, 0, 2 * Math.PI);
      ctx.fill();
    }
  });

  // Titulo
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 20px Arial';
  ctx.textAlign = 'left';
  const tituloBase = nombreMovimiento
    ? `Trayectorias Movimiento ${codigoMovimiento}: ${nombreMovimiento}`
    : `Trayectorias Movimiento ${codigoMovimiento}`;
  const titulo = descripcionMovimiento ? `${tituloBase} (${descripcionMovimiento})` : tituloBase;
  ctx.fillText(titulo, 20, 30);

  // Contador
  ctx.font = '16px Arial';
  ctx.fillText(`Total: ${eventosFiltrados.length} trayectorias`, 20, 55);

  return canvas.toDataURL('image/png');
}
