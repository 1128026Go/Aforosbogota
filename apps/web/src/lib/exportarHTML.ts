/**
 * Utilidad para exportar todas las tablas de aforo a un archivo HTML
 */

import type { DatosAforoPorMovimiento } from '@/types/aforo';

export function exportarAforoCompletoHTML(datos: DatosAforoPorMovimiento): void {
  const { metadata, volumenes_totales, movimientos } = datos;

  // Generar HTML completo
  const html = `
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aforo por Movimientos RILSA - ${metadata.ubicacion}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: #f5f7fa;
      padding: 40px 20px;
      color: #2c3e50;
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
    }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 40px;
      border-radius: 12px;
      margin-bottom: 40px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .header h1 {
      font-size: 32px;
      margin-bottom: 12px;
      font-weight: 700;
    }

    .header-meta {
      font-size: 14px;
      opacity: 0.95;
      line-height: 1.6;
    }

    .section {
      background: white;
      border-radius: 12px;
      padding: 32px;
      margin-bottom: 32px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      page-break-inside: avoid;
    }

    .section-title {
      font-size: 24px;
      font-weight: 700;
      color: #2c3e50;
      margin-bottom: 8px;
    }

    .section-subtitle {
      font-size: 14px;
      color: #7f8c8d;
      margin-bottom: 24px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      margin-top: 16px;
    }

    thead tr {
      background: #f9fafb;
      border-bottom: 2px solid #e5e7eb;
    }

    th {
      padding: 12px;
      text-align: left;
      font-weight: 600;
      color: #374151;
    }

    th.center {
      text-align: center;
    }

    tbody tr {
      border-bottom: 1px solid #f3f4f6;
    }

    tbody tr:nth-child(even) {
      background: #fafafa;
    }

    td {
      padding: 10px 12px;
    }

    td.center {
      text-align: center;
    }

    td.total {
      background: #f9fafb;
      font-weight: 600;
      color: #2c3e50;
    }

    .totals-row {
      background: #f0f9ff !important;
      font-weight: 600;
      border-top: 2px solid #3b82f6;
    }

    .footer {
      text-align: center;
      padding: 20px;
      color: #7f8c8d;
      font-size: 12px;
    }

    @media print {
      body {
        background: white;
        padding: 0;
      }

      .section {
        box-shadow: none;
        page-break-after: always;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📊 Aforo por Movimientos RILSA</h1>
      <div class="header-meta">
        <div><strong>Ubicación:</strong> ${metadata.ubicacion}</div>
        <div><strong>Fecha:</strong> ${metadata.fecha}</div>
        <div><strong>Periodo:</strong> ${metadata.hora_inicio} - ${metadata.hora_fin}</div>
      </div>
    </div>

    ${generarSeccionVolumenesTotales(volumenes_totales)}

    ${Object.values(movimientos)
      .sort((a, b) => a.codigo - b.codigo)
      .map(mov => generarSeccionMovimiento(mov))
      .join('\n')}

    <div class="footer">
      Generado el ${new Date().toLocaleString('es-CO')} • Sistema de Aforo RILSA
    </div>
  </div>
</body>
</html>
  `.trim();

  // Descargar archivo
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `Aforo_Completo_${metadata.fecha_iso}_${metadata.hora_inicio.replace(':', '')}.html`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function generarSeccionVolumenesTotales(volumenes: any): string {
  const { filas, totales } = volumenes;

  return `
    <div class="section">
      <h2 class="section-title">VOLUMENES TOTALES</h2>
      <p class="section-subtitle">Volumen vehicular total en intervalos de 15 minutos</p>

      <table>
        <thead>
          <tr>
            <th>Periodo (15 min)</th>
            <th class="center">🚗 Autos</th>
            <th class="center">🚌 Buses</th>
            <th class="center">🚚 Camiones</th>
            <th class="center">🏍️ Motos</th>
            <th class="center">🚲 Bicicletas</th>
            <th class="center total">Total</th>
          </tr>
        </thead>
        <tbody>
          ${filas.map((fila: any) => `
            <tr>
              <td><strong>${fila.periodo}</strong></td>
              <td class="center">${fila.autos}</td>
              <td class="center">${fila.buses}</td>
              <td class="center">${fila.camiones}</td>
              <td class="center">${fila.motos}</td>
              <td class="center">${fila.bicicletas}</td>
              <td class="center total">${fila.autos + fila.buses + fila.camiones + fila.motos + fila.bicicletas}</td>
            </tr>
          `).join('')}

          <tr class="totals-row">
            <td><strong>TOTALES</strong></td>
            <td class="center">${totales.autos}</td>
            <td class="center">${totales.buses}</td>
            <td class="center">${totales.camiones}</td>
            <td class="center">${totales.motos}</td>
            <td class="center">${totales.bicicletas}</td>
            <td class="center total">${totales.autos + totales.buses + totales.camiones + totales.motos + totales.bicicletas}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `;
}

function generarSeccionMovimiento(mov: any): string {
  const { codigo, nombre, tipo, filas, totales } = mov;

  const iconoTipo = {
    recto: '⬆️',
    giro_izquierda: '↰',
    giro_derecha: '↱',
    retorno_u: '↶',
  }[tipo] || '•';

  return `
    <div class="section">
      <h2 class="section-title">${iconoTipo} Movimiento RILSA ${codigo}: ${nombre}</h2>
      <p class="section-subtitle">Tipo: ${tipo.replace('_', ' ').toUpperCase()}</p>

      <table>
        <thead>
          <tr>
            <th>Periodo (15 min)</th>
            <th class="center">🚗 Autos</th>
            <th class="center">🚌 Buses</th>
            <th class="center">🚚 Camiones</th>
            <th class="center">🏍️ Motos</th>
            <th class="center">🚲 Bicicletas</th>
            <th class="center total">Total</th>
          </tr>
        </thead>
        <tbody>
          ${filas.map((fila: any) => `
            <tr>
              <td><strong>${fila.periodo}</strong></td>
              <td class="center">${fila.autos}</td>
              <td class="center">${fila.buses}</td>
              <td class="center">${fila.camiones}</td>
              <td class="center">${fila.motos}</td>
              <td class="center">${fila.bicicletas}</td>
              <td class="center total">${fila.autos + fila.buses + fila.camiones + fila.motos + fila.bicicletas}</td>
            </tr>
          `).join('')}

          <tr class="totals-row">
            <td><strong>TOTALES</strong></td>
            <td class="center">${totales.autos}</td>
            <td class="center">${totales.buses}</td>
            <td class="center">${totales.camiones}</td>
            <td class="center">${totales.motos}</td>
            <td class="center">${totales.bicicletas}</td>
            <td class="center total">${totales.autos + totales.buses + totales.camiones + totales.motos + totales.bicicletas}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `;
}
