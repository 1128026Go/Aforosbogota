import React, { useState, useEffect } from 'react';
import { useParams } from '../../main';
import { runValidation, getValidationResults, type ValidationResponse } from '../../api/validation-api';
import { LoadingSpinner } from '../../components/shared/LoadingSpinner';
import { Button } from '../../components/shared/Button';
import { Badge } from '../../components/shared/Badge';
import { Toast } from '../../components/shared/Toast';
import { StepNavigation } from '../../components/shared/StepNavigation';

export function DatasetValidationPage() {
  const { id: datasetId } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [results, setResults] = useState<ValidationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadPreviousResults();
  }, [datasetId]);

  const loadPreviousResults = async () => {
    try {
      setLoading(true);
      const data = await getValidationResults(datasetId!);
      if (data.results) {
        setResults({
          status: data.status,
          dataset_id: data.dataset_id,
          statistics: data.results.statistics,
          valid_count: data.results.statistics.valid,
          invalid_count: data.results.statistics.invalid,
          incomplete_count: data.results.statistics.incomplete_count || 0,
          errors_by_type: data.results.statistics.errors_by_type || {},
          validation_file: '',
          message: 'Resultados de validación previa'
        });
      }
    } catch (err: any) {
      // No es error si no hay resultados previos
      if (err.message && !err.message.includes('404')) {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRunValidation = async () => {
    try {
      setValidating(true);
      setError(null);
      const data = await runValidation(datasetId!, false);
      setResults(data);
      setToast({ message: data.message, type: 'success' });
    } catch (err: any) {
      setError(err.message || 'Error ejecutando validación');
      setToast({ message: err.message, type: 'error' });
    } finally {
      setValidating(false);
    }
  };

  if (loading && !results) return <LoadingSpinner />;

  return (
    <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Navegación por pasos */}
      <StepNavigation currentStepKey="validation" datasetId={datasetId} />
      
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header */}
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: '700', color: '#111827', marginBottom: '8px' }}>
            Validación de Trayectorias
          </h1>
          <p style={{ color: '#6b7280', fontSize: '16px' }}>
            {datasetId}
          </p>
        </div>
        <Button
          onClick={handleRunValidation}
          disabled={validating}
          variant="primary"
        >
          {validating ? 'Validando...' : 'Validar Dataset'}
        </Button>
      </div>

      {error && (
        <div style={{
          padding: '16px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          color: '#dc2626',
          marginBottom: '24px'
        }}>
          {error}
        </div>
      )}

      {results ? (
        <div style={{ display: 'grid', gap: '24px' }}>
          {/* Estadísticas Principales */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            padding: '24px'
          }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '24px' }}>
              Estadísticas de Validación
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
              <div>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Total</p>
                <p style={{ fontSize: '32px', fontWeight: '600', color: '#111827', margin: 0 }}>
                  {results.statistics.total.toLocaleString()}
                </p>
              </div>
              <div>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Válidas</p>
                <p style={{ fontSize: '32px', fontWeight: '600', color: '#10b981', margin: 0 }}>
                  {results.statistics.valid.toLocaleString()}
                </p>
                <div style={{ marginTop: '4px' }}>
                  <Badge variant="success">
                    {results.statistics.completion_rate.toFixed(1)}%
                  </Badge>
                </div>
              </div>
              <div>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Inválidas</p>
                <p style={{ fontSize: '32px', fontWeight: '600', color: '#ef4444', margin: 0 }}>
                  {results.statistics.invalid.toLocaleString()}
                </p>
              </div>
              <div>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Incompletas</p>
                <p style={{ fontSize: '32px', fontWeight: '600', color: '#f59e0b', margin: 0 }}>
                  {results.incomplete_count.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Errores por Tipo */}
          {Object.keys(results.errors_by_type).length > 0 && (
            <div style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              padding: '24px'
            }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
                Errores por Tipo
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                {Object.entries(results.errors_by_type).map(([type, count]) => (
                  <div key={type} style={{
                    padding: '12px',
                    backgroundColor: '#fef2f2',
                    borderRadius: '6px',
                    border: '1px solid #fecaca'
                  }}>
                    <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>{type}</p>
                    <p style={{ fontSize: '20px', fontWeight: '600', color: '#dc2626', margin: 0 }}>
                      {count}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mensaje de Resultado */}
          <div style={{
            padding: '16px',
            backgroundColor: results.statistics.completion_rate >= 80 ? '#f0fdf4' : '#fef3c7',
            border: `1px solid ${results.statistics.completion_rate >= 80 ? '#86efac' : '#fde047'}`,
            borderRadius: '8px'
          }}>
            <p style={{ margin: 0, color: results.statistics.completion_rate >= 80 ? '#166534' : '#92400e' }}>
              {results.message}
            </p>
          </div>
        </div>
      ) : (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          backgroundColor: 'white',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <p style={{ color: '#6b7280', marginBottom: '24px' }}>
            No hay resultados de validación. Ejecuta una validación para ver los resultados.
          </p>
          <Button onClick={handleRunValidation} disabled={validating} variant="primary">
            {validating ? 'Validando...' : 'Validar Dataset'}
          </Button>
        </div>
      )}
    </div>
  );
}




