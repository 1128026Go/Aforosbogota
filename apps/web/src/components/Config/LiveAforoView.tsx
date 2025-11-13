/**
 * Vista de Aforo en Vivo
 * Paso 3: Visualización de conteos por intervalos de 15 min + gráficas
 */

import React, { useEffect } from 'react';
import { useAforoLive } from '@/store/aforoLive';

const CLASES = ['car', 'motorcycle', 'bus', 'truck', 'bicycle', 'person'];
const CLASE_LABELS: Record<string, string> = {
  car: '🚗 Auto',
  motorcycle: '🏍️ Moto',
  bus: '🚌 Bus',
  truck: '🚚 Camión',
  bicycle: '🚲 Bici',
  person: '🚶 Peatón',
};

export default function LiveAforoView({ datasetId }: { datasetId: string }) {
  const { intervals, selectedInterval, currentData, loadIntervals, selectInterval, loadIntervalData } =
    useAforoLive();

  useEffect(() => {
    loadIntervals(datasetId);
  }, [datasetId, loadIntervals]);

  useEffect(() => {
    if (selectedInterval) {
      loadIntervalData(datasetId, selectedInterval);
    }
  }, [datasetId, selectedInterval, loadIntervalData]);

  const handleExportCSV = () => {
    if (!currentData) return;

    let csv = 'interval_start,mov_rilsa,clase,origin,dest,count\n';

    currentData.tracks.forEach((track) => {
      csv += `${currentData.interval_start},${track.mov_rilsa},${track.clase},${track.origin},${track.dest},1\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `aforo_${datasetId}_${selectedInterval?.replace(/:/g, '-')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div
        style={{
          background: 'white',
          borderRadius: '12px',
          padding: '32px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>📊</div>
            <h2 style={{ fontSize: '24px', color: '#2c3e50', marginBottom: '8px' }}>
              Aforo en Vivo - Intervalos de 15 Minutos
            </h2>
            <p style={{ fontSize: '14px', color: '#7f8c8d' }}>
              {intervals.length} intervalo{intervals.length !== 1 ? 's' : ''} disponible
              {intervals.length !== 1 ? 's' : ''}
            </p>
          </div>

          {selectedInterval && currentData && (
            <button
              onClick={handleExportCSV}
              style={{
                padding: '12px 24px',
                background: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              💾 Exportar CSV
            </button>
          )}
        </div>

        {/* Interval selector */}
        {intervals.length > 0 && (
          <div style={{ marginTop: '24px' }}>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#6b7280' }}>
              Seleccionar Intervalo:
            </label>
            <select
              value={selectedInterval || ''}
              onChange={(e) => selectInterval(e.target.value)}
              style={{
                padding: '10px 16px',
                border: '1px solid #e0e0e0',
                borderRadius: '6px',
                fontSize: '14px',
                minWidth: '300px',
              }}
            >
              {intervals.map((interval) => (
                <option key={interval} value={interval}>
                  {new Date(interval).toLocaleString('es-CO', {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Empty state */}
      {intervals.length === 0 && (
        <div
          style={{
            background: 'white',
            borderRadius: '12px',
            padding: '60px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '64px', marginBottom: '24px' }}>⏳</div>
          <h3 style={{ fontSize: '20px', color: '#2c3e50', marginBottom: '12px' }}>
            Esperando trayectorias...
          </h3>
          <p style={{ fontSize: '14px', color: '#7f8c8d' }}>
            Los conteos aparecerán automáticamente cuando se completen trayectorias
          </p>
        </div>
      )}

      {/* Data table */}
      {currentData && (
        <div
          style={{
            background: 'white',
            borderRadius: '12px',
            padding: '32px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <h3 style={{ fontSize: '18px', color: '#2c3e50', marginBottom: '24px', fontWeight: '600' }}>
            Conteos por Movimiento RILSA × Clase
          </h3>

          {/* Summary */}
          <div style={{ display: 'flex', gap: '16px', marginBottom: '32px', flexWrap: 'wrap' }}>
            {CLASES.map((clase) => {
              const total = Object.entries(currentData.counts)
                .filter(([key]) => key.endsWith(`_${clase}`))
                .reduce((sum, [, count]) => sum + count, 0);

              if (total === 0) return null;

              return (
                <div
                  key={clase}
                  style={{
                    padding: '12px 20px',
                    background: '#f9fafb',
                    borderRadius: '6px',
                    border: '1px solid #e5e7eb',
                  }}
                >
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
                    {CLASE_LABELS[clase]}
                  </div>
                  <div style={{ fontSize: '20px', color: '#2c3e50', fontWeight: '600' }}>
                    {total}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Mov. RILSA</th>
                  {CLASES.map((clase) => (
                    <th key={clase} style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>
                      {CLASE_LABELS[clase]}
                    </th>
                  ))}
                  <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {[1, 2, 3, 4, 5, 6, 7, 8, 91, 92, 93, 94, 101, 102, 103, 104].map((mov) => {
                  const rowTotal = CLASES.reduce((sum, clase) => {
                    const key = `${mov}_${clase}`;
                    return sum + (currentData.counts[key] || 0);
                  }, 0);

                  // Generar label según el código
                  let label = `RILSA ${mov}`;
                  if (mov >= 91 && mov <= 94) {
                    label = `RILSA 9(${mov - 90})`;
                  } else if (mov >= 101 && mov <= 104) {
                    label = `RILSA 10(${mov - 100})`;
                  }

                  return (
                    <tr
                      key={mov}
                      style={{
                        borderBottom: '1px solid #f3f4f6',
                        opacity: rowTotal === 0 ? 0.4 : 1,
                      }}
                    >
                      <td style={{ padding: '12px', fontWeight: '600' }}>{label}</td>
                      {CLASES.map((clase) => {
                        const key = `${mov}_${clase}`;
                        const count = currentData.counts[key] || 0;
                        return (
                          <td
                            key={clase}
                            style={{
                              padding: '12px',
                              textAlign: 'center',
                              background: count > 0 ? '#f0fdf4' : 'transparent',
                              fontWeight: count > 0 ? '600' : 'normal',
                              color: count > 0 ? '#166534' : '#9ca3af',
                            }}
                          >
                            {count || '-'}
                          </td>
                        );
                      })}
                      <td
                        style={{
                          padding: '12px',
                          textAlign: 'center',
                          background: '#f9fafb',
                          fontWeight: '600',
                        }}
                      >
                        {rowTotal || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Total tracks */}
          <div style={{ marginTop: '24px', padding: '16px', background: '#f9fafb', borderRadius: '6px' }}>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>Total de trayectorias en este intervalo:</div>
            <div style={{ fontSize: '24px', color: '#2c3e50', fontWeight: '600', marginTop: '4px' }}>
              {currentData.tracks.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
