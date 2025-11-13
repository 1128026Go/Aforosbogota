import React, { useEffect, useState } from 'react';
import { useParams } from '../../main';
import { getHistory } from '../../api/dataset-editor-api';
import { LoadingSpinner } from '../../components/shared/LoadingSpinner';
import { StepNavigation } from '../../components/shared/StepNavigation';

export function DatasetHistoryPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const { history: data } = await getHistory(datasetId);
        setHistory(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [datasetId]);

  if (loading) return <LoadingSpinner />;

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Navegación por pasos */}
      <StepNavigation currentStepKey="history" datasetId={datasetId} />
      
      <h1 style={{ fontSize: '28px', fontWeight: '600', marginBottom: '8px' }}>
        Historial de Cambios
      </h1>
      <p style={{ color: '#6b7280', marginBottom: '32px' }}>{datasetId}</p>

      {/* Timeline */}
      <div style={{ position: 'relative', paddingLeft: '40px' }}>
        {/* Línea vertical */}
        <div style={{
          position: 'absolute',
          left: '15px',
          top: 0,
          bottom: 0,
          width: '2px',
          backgroundColor: '#e5e7eb',
        }} />

        {history.map((entry, idx) => (
          <div key={idx} style={{ position: 'relative', marginBottom: '32px' }}>
            {/* Punto en la línea */}
            <div style={{
              position: 'absolute',
              left: '-33px',
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: '#3b82f6',
              border: '3px solid white',
              boxShadow: '0 0 0 2px #3b82f6',
            }} />

            {/* Contenido */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            }}>
              <div style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#111827' }}>
                    {entry.action}
                  </h3>
                  <span style={{ fontSize: '13px', color: '#6b7280' }}>
                    {new Date(entry.timestamp).toLocaleString('es-ES')}
                  </span>
                </div>
                <p style={{ fontSize: '13px', color: '#6b7280', marginTop: '4px' }}>
                  Por: {entry.user}
                </p>
              </div>

              {entry.details && entry.details.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <strong style={{ fontSize: '14px', color: '#374151' }}>Detalles:</strong>
                  <ul style={{ marginTop: '8px', paddingLeft: '20px', color: '#6b7280', fontSize: '13px' }}>
                    {entry.details.map((detail: string, i: number) => (
                      <li key={i}>{detail}</li>
                    ))}
                  </ul>
                </div>
              )}

              {entry.rules_applied && entry.rules_applied.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <strong style={{ fontSize: '14px', color: '#374151' }}>Reglas aplicadas:</strong>
                  <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {entry.rules_applied.map((ruleId: string, i: number) => (
                      <span
                        key={i}
                        style={{
                          backgroundColor: '#e0f2fe',
                          color: '#0369a1',
                          padding: '4px 12px',
                          borderRadius: '9999px',
                          fontSize: '12px',
                        }}
                      >
                        {ruleId}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {history.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px', color: '#6b7280' }}>
          <p>No hay cambios registrados</p>
        </div>
      )}
    </div>
  );
}
