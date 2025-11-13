import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from '../../main';
import { generateConfig, viewConfig, updatePolygons, type ConfigViewResponse } from '../../api/config-api';
import { generateRilsaReport, downloadReportFile, getReportDownloadUrl } from '../../api/rilsa-api';
import { LoadingSpinner } from '../../components/shared/LoadingSpinner';
import { Button } from '../../components/shared/Button';
import { Badge } from '../../components/shared/Badge';
import { Toast } from '../../components/shared/Toast';
import { StepNavigation } from '../../components/shared/StepNavigation';

export function DatasetConfigPage() {
  const { id: datasetId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [config, setConfig] = useState<ConfigViewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    loadConfig();
  }, [datasetId]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await viewConfig(datasetId!);
      setConfig(data);
    } catch (err: any) {
      setError(err.message || 'Error cargando configuración');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateConfig = async () => {
    try {
      setGenerating(true);
      setError(null);
      const result = await generateConfig(datasetId!);
      setToast({ message: result.message, type: 'success' });
      await loadConfig(); // Recargar configuración
    } catch (err: any) {
      setError(err.message || 'Error generando configuración');
      setToast({ message: err.message, type: 'error' });
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      setError(null);
      const result = await generateRilsaReport(datasetId!, 'csv', true);
      setToast({ message: 'Reporte generado exitosamente', type: 'success' });
      
      // Descargar archivos CSV
      if (result.csv_files && result.csv_files.length > 0) {
        for (const filename of result.csv_files) {
          const blob = await downloadReportFile(datasetId!, filename.split('/').pop()!);
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename.split('/').pop()!;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Error generando reporte');
      setToast({ message: err.message, type: 'error' });
    } finally {
      setGeneratingReport(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Navegación por pasos */}
      <StepNavigation currentStepKey="config" datasetId={datasetId} />
      
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
            Configuración del Dataset
          </h1>
          <p style={{ color: '#6b7280', fontSize: '16px' }}>
            {datasetId}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            onClick={handleGenerateConfig}
            disabled={generating}
            variant="primary"
          >
            {generating ? 'Generando...' : 'Regenerar Configuración'}
          </Button>
          <Button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            variant="success"
          >
            {generatingReport ? 'Generando...' : 'Generar Reporte RILSA'}
          </Button>
        </div>
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

      {!config ? (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          backgroundColor: 'white',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <p style={{ color: '#6b7280', marginBottom: '24px' }}>
            No hay configuración disponible. Genera una configuración automática.
          </p>
          <Button onClick={handleGenerateConfig} disabled={generating} variant="primary">
            {generating ? 'Generando...' : 'Generar Configuración'}
          </Button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Configuración de Cardinales */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            padding: '24px'
          }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
              Accesos Cardinales
            </h2>
            <div style={{ display: 'grid', gap: '12px' }}>
              {Object.entries(config.config.cardinal_config.accesses || {}).map(([cardinal, access]: [string, any]) => (
                <div key={cardinal} style={{
                  padding: '16px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '600' }}>{cardinal}</h3>
                    <Badge variant="success">{access.name || `Acceso ${cardinal}`}</Badge>
                  </div>
                  {access.entry_polygon && (
                    <p style={{ fontSize: '12px', color: '#6b7280', margin: '4px 0' }}>
                      Entrada: {access.entry_polygon.length} puntos
                    </p>
                  )}
                  {access.exit_polygon && (
                    <p style={{ fontSize: '12px', color: '#6b7280', margin: '4px 0' }}>
                      Salida: {access.exit_polygon.length} puntos
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Movimientos Inferidos */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            padding: '24px'
          }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
              Movimientos Inferidos
            </h2>
            <div style={{ display: 'grid', gap: '8px' }}>
              {Object.entries(config.inferred_movements || {}).map(([key, movement]: [string, any]) => (
                <div key={key} style={{
                  padding: '12px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}>
                  <strong>{key}</strong>: Código {movement.code} ({movement.type})
                </div>
              ))}
            </div>
            {Object.keys(config.inferred_movements || {}).length === 0 && (
              <p style={{ color: '#6b7280', fontSize: '14px', fontStyle: 'italic' }}>
                No hay movimientos inferidos
              </p>
            )}
          </div>

          {/* Resumen Ejecutivo */}
          {config.config && (
            <div style={{
              gridColumn: '1 / -1',
              backgroundColor: 'white',
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              padding: '24px'
            }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
                Resumen de Configuración
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                <div>
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Accesos</p>
                  <p style={{ fontSize: '24px', fontWeight: '600', color: '#3b82f6', margin: 0 }}>
                    {Object.keys(config.config.cardinal_config.accesses || {}).length}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Movimientos</p>
                  <p style={{ fontSize: '24px', fontWeight: '600', color: '#10b981', margin: 0 }}>
                    {Object.keys(config.inferred_movements || {}).length}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Reglas</p>
                  <p style={{ fontSize: '24px', fontWeight: '600', color: '#f59e0b', margin: 0 }}>
                    {config.config.correction_rules?.length || 0}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Filtros</p>
                  <p style={{ fontSize: '24px', fontWeight: '600', color: '#8b5cf6', margin: 0 }}>
                    {Object.keys(config.config.trajectory_filters || {}).length}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}




