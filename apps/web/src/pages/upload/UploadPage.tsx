/**
 * Página de Upload de PKL
 * Primera pantalla del flujo
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from '@/main';
import { useDatasets } from '@/store/datasets';
import { StepNavigation } from '@/components/shared/StepNavigation';

interface DatasetItem {
  id: string;
  name: string;
  created_at?: string;
  frames?: number;
}

export default function UploadPage() {
  const navigate = useNavigate();
  const { uploadDataset, datasets, loadDatasets } = useDatasets();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingList, setLoadingList] = useState(false);

  // Cargar biblioteca de datasets al entrar
  useEffect(() => {
    const fetchDatasets = async () => {
      setLoadingList(true);
      try {
        await loadDatasets();
      } catch (error) {
        console.error('Error cargando datasets:', error);
      } finally {
        setLoadingList(false);
      }
    };
    fetchDatasets();
  }, [loadDatasets]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.pkl')) {
        setError('Solo se aceptan archivos .pkl');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const datasetId = await uploadDataset(file);
      
      // Mostrar mensaje de éxito y redirigir automáticamente al siguiente paso
      setError('✅ Dataset subido exitosamente. Redirigiendo a configuración...');
      
      // Recargar biblioteca para mostrar el nuevo dataset
      await loadDatasets();
      
      // Redirect automático al siguiente paso (configuración) después de 1.5 segundos
      setTimeout(() => {
        navigate(`/datasets/${datasetId}/config`);
      }, 1500);
      
    } catch (err) {
      setError('Error al subir el archivo. Verifica que sea un PKL válido.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  // Función para abrir un dataset existente
  const handleOpenDataset = (datasetId: string) => {
    navigate(`/datasets/${datasetId}/config`);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      {/* Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '20px 40px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        }}
      >
        <h1 style={{ color: 'white', fontSize: '28px', margin: 0 }}>
          📊 Aforo Integrado
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.9)', margin: '8px 0 0 0', fontSize: '14px' }}>
          Subir dataset de trayectorias
        </p>
      </div>

      {/* Content */}
      <div style={{ padding: '60px 40px', maxWidth: '800px', margin: '0 auto' }}>
        {/* Navegación por pasos */}
        <StepNavigation currentStepKey="upload" datasetId={undefined} />
        
        {/* Resto del contenido */}
        <div
          style={{
            background: 'white',
            borderRadius: '12px',
            padding: '40px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{ fontSize: '64px', marginBottom: '16px' }}>📦</div>
            <h2 style={{ fontSize: '24px', color: '#2c3e50', marginBottom: '8px' }}>
              Subir Dataset PKL
            </h2>
            <p style={{ fontSize: '14px', color: '#7f8c8d' }}>
              Selecciona un archivo .pkl con trayectorias procesadas
            </p>
          </div>

          {/* File input */}
          <div
            style={{
              border: '2px dashed #e0e0e0',
              borderRadius: '8px',
              padding: '40px',
              textAlign: 'center',
              marginBottom: '24px',
              background: file ? '#f0fdf4' : '#fafafa',
              transition: 'all 0.3s',
            }}
          >
            <input
              type="file"
              accept=".pkl"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              id="file-input"
              disabled={uploading}
            />
            <label
              htmlFor="file-input"
              style={{
                display: 'inline-block',
                padding: '12px 24px',
                background: '#667eea',
                color: 'white',
                borderRadius: '6px',
                cursor: uploading ? 'not-allowed' : 'pointer',
                fontWeight: '600',
                opacity: uploading ? 0.6 : 1,
              }}
            >
              {file ? '📁 Cambiar archivo' : '📁 Seleccionar PKL'}
            </label>

            {file && (
              <div style={{ marginTop: '16px' }}>
                <p style={{ fontSize: '14px', color: '#2c3e50', fontWeight: '600' }}>
                  ✓ {file.name}
                </p>
                <p style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px' }}>
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div
              style={{
                padding: '12px 16px',
                background: '#fee',
                border: '1px solid #fcc',
                borderRadius: '6px',
                color: '#c33',
                fontSize: '14px',
                marginBottom: '24px',
              }}
            >
              ⚠️ {error}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={() => navigate('/library')}
              disabled={uploading}
              style={{
                flex: 1,
                padding: '14px',
                background: '#f3f4f6',
                border: 'none',
                borderRadius: '6px',
                fontSize: '15px',
                fontWeight: '600',
                cursor: uploading ? 'not-allowed' : 'pointer',
                color: '#6b7280',
                opacity: uploading ? 0.6 : 1,
              }}
            >
              📚 Ir a Biblioteca
            </button>
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              style={{
                flex: 2,
                padding: '14px',
                background: file && !uploading ? '#10b981' : '#d1d5db',
                border: 'none',
                borderRadius: '6px',
                fontSize: '15px',
                fontWeight: '600',
                cursor: file && !uploading ? 'pointer' : 'not-allowed',
                color: 'white',
              }}
            >
              {uploading ? '⏳ Subiendo...' : '🚀 Subir y Configurar'}
            </button>
          </div>
        </div>

        {/* Biblioteca de Datasets */}
        <div
          style={{
            background: 'white',
            borderRadius: '12px',
            padding: '40px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginTop: '24px',
          }}
        >
          <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h3 style={{ fontSize: '20px', color: '#2c3e50', margin: 0 }}>
              📚 Biblioteca de Datasets
            </h3>
            {loadingList && (
              <span style={{ fontSize: '14px', color: '#7f8c8d' }}>Cargando...</span>
            )}
          </div>

          {datasets.length === 0 && !loadingList && (
            <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📂</div>
              <p style={{ fontSize: '16px' }}>
                Aún no hay datasets registrados. Sube tu primer PKL arriba.
              </p>
            </div>
          )}

          {datasets.length > 0 && (
            <div style={{ 
              display: 'grid', 
              gap: '16px', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' 
            }}>
              {datasets.map((dataset) => (
                <button
                  key={dataset.id}
                  type="button"
                  onClick={() => handleOpenDataset(dataset.id)}
                  style={{
                    border: '1px solid #e0e0e0',
                    borderRadius: '8px',
                    padding: '16px',
                    textAlign: 'left',
                    background: 'white',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  <div style={{ fontWeight: '600', fontSize: '16px', color: '#2c3e50', marginBottom: '8px' }}>
                    📊 {dataset.name || dataset.id}
                  </div>
                  {dataset.frames && (
                    <div style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '4px' }}>
                      {dataset.frames.toLocaleString()} frames
                    </div>
                  )}
                  {dataset.created_at && (
                    <div style={{ fontSize: '12px', color: '#95a5a6' }}>
                      Creado: {new Date(dataset.created_at).toLocaleDateString()}
                    </div>
                  )}
                  <div style={{ 
                    marginTop: '12px', 
                    fontSize: '12px', 
                    color: '#667eea', 
                    fontWeight: '600' 
                  }}>
                    Click para continuar →
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
