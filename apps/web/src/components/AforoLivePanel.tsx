/**
 * Panel flotante de aforo en vivo
 * Muestra conteos agregados por bloques de 15 minutos
 */

import React, { useMemo } from 'react';
import { useAforoLive } from '../store/aforoLive';
import { getNombreMovimiento, getEmojiMovimiento } from '../lib/rilsa';
import type { ClaseMovil, CountKey } from '../types/aforo';

// Emojis para clases vehiculares
const CLASE_EMOJIS: Record<ClaseMovil, string> = {
  car: '🚗',
  truck: '🚚',
  bus: '🚌',
  motorcycle: '🏍️',
  bicycle: '🚲',
  person: '🚶',
};

const CLASES_ORDEN: ClaseMovil[] = ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'person'];

export default function AforoLivePanel() {
  const bucketData = useAforoLive((s) => s.getCurrentBucketData());
  const allBuckets = useAforoLive((s) => s.getAllBuckets());
  const setCurrentBucket = useAforoLive((s) => s.setCurrentBucket);
  const exportCSV = useAforoLive((s) => s.exportBucketToCSV);
  const reset = useAforoLive((s) => s.reset);

  // Procesar datos para tabla
  const tableData = useMemo(() => {
    if (!bucketData) return [];

    const rows: {
      mov: number;
      totales: Record<ClaseMovil, number>;
      totalMov: number;
    }[] = [];

    // Crear filas para movimientos 1-10
    for (let mov = 1; mov <= 10; mov++) {
      const totales: Record<ClaseMovil, number> = {
        car: 0,
        truck: 0,
        bus: 0,
        motorcycle: 0,
        bicycle: 0,
        person: 0,
      };

      CLASES_ORDEN.forEach((clase) => {
        const key: CountKey = { movimiento_rilsa: mov, clase };
        const keyStr = JSON.stringify(key);
        totales[clase] = bucketData.counts[keyStr] ?? 0;
      });

      const totalMov = Object.values(totales).reduce((a, b) => a + b, 0);

      rows.push({ mov, totales, totalMov });
    }

    return rows;
  }, [bucketData]);

  // Totales por clase
  const totalesPorClase = useMemo(() => {
    const totales: Record<ClaseMovil, number> = {
      car: 0,
      truck: 0,
      bus: 0,
      motorcycle: 0,
      bicycle: 0,
      person: 0,
    };

    tableData.forEach((row) => {
      CLASES_ORDEN.forEach((clase) => {
        totales[clase] += row.totales[clase];
      });
    });

    return totales;
  }, [tableData]);

  // Manejar exportación CSV
  const handleExport = () => {
    if (!bucketData) return;

    const csv = exportCSV(bucketData.key.bucket_iso);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `aforo_${bucketData.key.bucket_iso.replace(/:/g, '-')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Formato de hora para display
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
  };

  if (!bucketData) {
    return (
      <div className="aforo-panel aforo-panel--empty">
        <div className="aforo-panel__header">
          <h3>📊 Aforo en Vivo</h3>
        </div>
        <div className="aforo-panel__body">
          <p>Esperando trayectorias...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="aforo-panel">
      {/* Header */}
      <div className="aforo-panel__header">
        <div>
          <h3>📊 Aforo en Vivo</h3>
          <div className="aforo-panel__meta">
            <span className="badge">
              {formatTime(bucketData.start)} - {formatTime(bucketData.end)}
            </span>
            <span className="badge badge--period">{bucketData.key.periodo}</span>
            <span className="badge badge--ramal">Ramal {bucketData.key.ramal}</span>
            <span className="badge badge--total">Total: {bucketData.total}</span>
          </div>
        </div>

        {/* Selector de bucket */}
        {allBuckets.length > 1 && (
          <select
            className="bucket-selector"
            value={bucketData.key.bucket_iso}
            onChange={(e) => setCurrentBucket(e.target.value)}
          >
            {allBuckets.map((bucket) => {
              const key = JSON.parse(bucket);
              const start = new Date(key.bucket_iso);
              return (
                <option key={bucket} value={bucket}>
                  {formatTime(start)} - {formatTime(new Date(start.getTime() + 15 * 60000))}
                </option>
              );
            })}
          </select>
        )}
      </div>

      {/* Tabla de conteos */}
      <div className="aforo-panel__body">
        <div className="aforo-table-container">
          <table className="aforo-table">
            <thead>
              <tr>
                <th>Mov</th>
                {CLASES_ORDEN.map((clase) => (
                  <th key={clase} title={clase}>
                    {CLASE_EMOJIS[clase]}
                  </th>
                ))}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {tableData.map((row) => (
                <tr key={row.mov} className={row.totalMov === 0 ? 'row-empty' : ''}>
                  <td>
                    <span className="mov-label" title={getNombreMovimiento(row.mov)}>
                      {getEmojiMovimiento(row.mov)} {row.mov}
                    </span>
                  </td>
                  {CLASES_ORDEN.map((clase) => (
                    <td key={clase} className={row.totales[clase] > 0 ? 'cell-active' : ''}>
                      {row.totales[clase] || '-'}
                    </td>
                  ))}
                  <td className="cell-total">{row.totalMov || '-'}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="row-totals">
                <td>
                  <strong>Total</strong>
                </td>
                {CLASES_ORDEN.map((clase) => (
                  <td key={clase}>
                    <strong>{totalesPorClase[clase]}</strong>
                  </td>
                ))}
                <td className="cell-total">
                  <strong>{bucketData.total}</strong>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Footer con acciones */}
      <div className="aforo-panel__footer">
        <button onClick={handleExport} className="btn btn--primary">
          💾 Exportar CSV
        </button>
        <button onClick={reset} className="btn btn--danger">
          🔄 Reset
        </button>
      </div>

      {/* Estilos inline (mover a CSS externo en producción) */}
      <style>{`
        .aforo-panel {
          position: fixed;
          top: 20px;
          right: 20px;
          width: 600px;
          max-height: 80vh;
          background: white;
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
          display: flex;
          flex-direction: column;
          z-index: 1000;
          font-family: system-ui, -apple-system, sans-serif;
        }

        .aforo-panel--empty {
          padding: 20px;
          text-align: center;
        }

        .aforo-panel__header {
          padding: 16px 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .aforo-panel__header h3 {
          margin: 0 0 8px 0;
          font-size: 18px;
          color: #111827;
        }

        .aforo-panel__meta {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .badge {
          display: inline-block;
          padding: 4px 8px;
          background: #f3f4f6;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .badge--period {
          background: #dbeafe;
          color: #1e40af;
        }

        .badge--ramal {
          background: #fef3c7;
          color: #92400e;
        }

        .badge--total {
          background: #d1fae5;
          color: #065f46;
        }

        .bucket-selector {
          padding: 6px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 13px;
          margin-top: 8px;
        }

        .aforo-panel__body {
          flex: 1;
          overflow: auto;
          padding: 16px 20px;
        }

        .aforo-table-container {
          overflow-x: auto;
        }

        .aforo-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }

        .aforo-table th {
          background: #f9fafb;
          padding: 8px 12px;
          text-align: center;
          font-weight: 600;
          border-bottom: 2px solid #e5e7eb;
        }

        .aforo-table td {
          padding: 8px 12px;
          text-align: center;
          border-bottom: 1px solid #f3f4f6;
        }

        .aforo-table tbody tr:hover {
          background: #fafafa;
        }

        .row-empty {
          opacity: 0.4;
        }

        .cell-active {
          background: #f0fdf4;
          font-weight: 600;
          color: #166534;
        }

        .cell-total {
          background: #f9fafb;
          font-weight: 600;
        }

        .row-totals {
          background: #f3f4f6;
        }

        .mov-label {
          font-weight: 500;
        }

        .aforo-panel__footer {
          padding: 16px 20px;
          border-top: 1px solid #e5e7eb;
          display: flex;
          gap: 12px;
        }

        .btn {
          flex: 1;
          padding: 10px 16px;
          border: none;
          border-radius: 6px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn--primary {
          background: #3b82f6;
          color: white;
        }

        .btn--primary:hover {
          background: #2563eb;
        }

        .btn--danger {
          background: #ef4444;
          color: white;
        }

        .btn--danger:hover {
          background: #dc2626;
        }
      `}</style>
    </div>
  );
}
