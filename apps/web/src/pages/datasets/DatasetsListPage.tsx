import React, { useState } from 'react';
import { useNavigate } from '../../main';
import { useDatasets } from '../../hooks/useDatasets';
import { uploadDataset } from '../../api/datasets-api';
import { LoadingSpinner } from '../../components/shared/LoadingSpinner';
import { Badge } from '../../components/shared/Badge';
import { Button } from '../../components/shared/Button';

export function DatasetsListPage() {
  const navigate = useNavigate();
  const { datasets, loading, error, refetch } = useDatasets();
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setUploadMessage(null);
      const result = await uploadDataset(file);
      setUploadMessage(`✅ Dataset ${result.name} subido exitosamente. Redirigiendo al editor...`);
      
      // Recargar la lista de datasets
      await refetch();
      
      // Redirigir al editor automáticamente después de 1.5 segundos
      setTimeout(() => {
        navigate(`/datasets/${result.id}/editor`);
      }, 1500);
      
    } catch (err: any) {
      setUploadMessage(`❌ Error: ${err.message}`);
    } finally {
      setUploading(false);
      // Limpiar el input
      event.target.value = '';
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div style={{ padding: '40px', color: '#ef4444' }}>Error: {error}</div>;

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
          <div>
            <h1 style={{ fontSize: '32px', fontWeight: '700', color: '#111827', marginBottom: '8px' }}>
              Gestión de Datasets
            </h1>
            <p style={{ color: '#6b7280', fontSize: '16px' }}>
              Edita, configura y administra tus datasets de tráfico vehicular
            </p>
          </div>
          <div>
            <label style={{
              display: 'inline-block',
              padding: '10px 16px',
              backgroundColor: uploading ? '#6b7280' : '#3b82f6',
              color: 'white',
              borderRadius: '8px',
              cursor: uploading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'background-color 0.2s',
            }}>
              {uploading ? 'Subiendo...' : '📁 Subir PKL'}
              <input
                type="file"
                accept=".pkl"
                onChange={handleFileUpload}
                disabled={uploading}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        </div>

        {/* Mensaje de upload */}
        {uploadMessage && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '8px',
            backgroundColor: uploadMessage.startsWith('Error') ? '#fef2f2' : '#f0f9ff',
            border: `1px solid ${uploadMessage.startsWith('Error') ? '#fecaca' : '#bae6fd'}`,
            color: uploadMessage.startsWith('Error') ? '#dc2626' : '#0369a1',
            marginBottom: '16px'
          }}>
            {uploadMessage}
          </div>
        )}
      </div>

      {/* Grid de datasets */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '24px' }}>
        {datasets.map((dataset) => (
          <div
            key={dataset.dataset_id}
            style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              padding: '24px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              border: '1px solid #e5e7eb',
            }}
            onClick={() => navigate(`/datasets/${dataset.dataset_id}/editor`)}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            {/* Header del card */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', margin: 0 }}>
                  {dataset.dataset_id}
                </h3>
                {dataset.has_config ? (
                  <Badge variant="success">Configurado</Badge>
                ) : (
                  <Badge variant="warning">Sin configurar</Badge>
                )}
              </div>
              {dataset.pkl_file && (
                <p style={{ fontSize: '13px', color: '#6b7280', margin: 0 }}>{dataset.pkl_file}</p>
              )}
            </div>

            {/* Estadísticas */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
              <div>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Eventos</p>
                <p style={{ fontSize: '24px', fontWeight: '600', color: '#3b82f6', margin: 0 }}>
                  {dataset.events_count.toLocaleString()}
                </p>
              </div>
              <div>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 4px 0' }}>Reglas</p>
                <p style={{ fontSize: '24px', fontWeight: '600', color: '#10b981', margin: 0 }}>
                  {dataset.rules_count}
                </p>
              </div>
            </div>

            {/* Fecha */}
            {dataset.last_modified && (
              <div style={{ paddingTop: '16px', borderTop: '1px solid #e5e7eb' }}>
                <p style={{ fontSize: '12px', color: '#9ca3af', margin: 0 }}>
                  Última modificación: {new Date(dataset.last_modified).toLocaleString('es-ES')}
                </p>
              </div>
            )}

            {/* Botones de acción */}
            <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
              <Button
                size="sm"
                variant="primary"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/datasets/${dataset.dataset_id}/editor`);
                }}
              >
                Editor
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/datasets/${dataset.dataset_id}/rules`);
                }}
              >
                Reglas
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/datasets/${dataset.dataset_id}/history`);
                }}
              >
                Historial
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty state */}
      {datasets.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#6b7280' }}>
          <p style={{ fontSize: '18px', marginBottom: '8px' }}>No hay datasets disponibles</p>
          <p style={{ fontSize: '14px' }}>Sube un archivo PKL para comenzar</p>
        </div>
      )}
    </div>
  );
}
