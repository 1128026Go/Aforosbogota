/**
 * Página de Biblioteca de Datasets
 * Lista todos los PKLs subidos
 */

import React, { useEffect } from 'react';
import { useNavigate } from '@/main';
import { useDatasets } from '@/store/datasets';
import { API_BASE_URL } from '@/config/api';

export default function LibraryPage() {
  const navigate = useNavigate();
  const { datasets, loadDatasets } = useDatasets();

  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);

  const handleDelete = async (e: React.MouseEvent, datasetId: string, datasetName: string) => {
    e.stopPropagation(); // Evitar que se active el click del card

    if (!confirm(`¿Estás seguro de eliminar el dataset "${datasetName}"?\n\nEsta acción no se puede deshacer.`)) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}`, {
        method: 'DELETE',
      });

      if (!res.ok) throw new Error('Error eliminando dataset');

      alert('Dataset eliminado exitosamente');
      loadDatasets(); // Recargar lista
    } catch (error) {
      console.error('Error:', error);
      alert('Error al eliminar el dataset');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      {/* Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '20px 40px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <h1 style={{ color: 'white', fontSize: '28px', margin: 0 }}>
            📚 Biblioteca de Aforos
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.9)', margin: '8px 0 0 0', fontSize: '14px' }}>
            {datasets.length} dataset{datasets.length !== 1 ? 's' : ''} disponible
            {datasets.length !== 1 ? 's' : ''}
          </p>
        </div>

        <button
          onClick={() => navigate('/upload')}
          style={{
            padding: '10px 20px',
            background: 'rgba(255,255,255,0.2)',
            color: 'white',
            border: '2px solid rgba(255,255,255,0.3)',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.3)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
          }}
        >
          📦 Subir Nuevo
        </button>
      </div>

      {/* Content */}
      <div style={{ padding: '40px' }}>
        {datasets.length === 0 ? (
          <div
            style={{
              padding: '80px',
              textAlign: 'center',
              background: 'white',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ fontSize: '64px', marginBottom: '24px' }}>📭</div>
            <h2 style={{ fontSize: '24px', color: '#2c3e50', marginBottom: '16px' }}>
              No hay datasets aún
            </h2>
            <p style={{ fontSize: '16px', color: '#7f8c8d', marginBottom: '32px' }}>
              Sube tu primer archivo PKL para comenzar
            </p>
            <button
              onClick={() => navigate('/upload')}
              style={{
                padding: '14px 28px',
                background: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '15px',
                fontWeight: '600',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
            >
              📦 Subir Dataset
            </button>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: '24px',
            }}
          >
            {datasets.map((dataset) => (
              <div
                key={dataset.id}
                onClick={() => navigate(`/aforo/${dataset.id}`)}
                style={{
                  background: 'white',
                  borderRadius: '12px',
                  padding: '24px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  border: '2px solid transparent',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.15)';
                  e.currentTarget.style.borderColor = '#667eea';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                  e.currentTarget.style.borderColor = 'transparent';
                }}
              >
                {/* Icon */}
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>

                {/* Name */}
                <h3
                  style={{
                    fontSize: '18px',
                    color: '#2c3e50',
                    marginBottom: '8px',
                    fontWeight: '600',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                  title={dataset.name}
                >
                  {dataset.name}
                </h3>

                {/* Stats */}
                <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#7f8c8d' }}>Frames</div>
                    <div style={{ fontSize: '16px', color: '#2c3e50', fontWeight: '600' }}>
                      {dataset.frames.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#7f8c8d' }}>Tracks</div>
                    <div style={{ fontSize: '16px', color: '#2c3e50', fontWeight: '600' }}>
                      {dataset.tracks.toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Date */}
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '12px' }}>
                  {new Date(dataset.created_at).toLocaleString('es-CO', {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}
                </div>

                {/* ID */}
                <div
                  style={{
                    fontSize: '11px',
                    color: '#a0aec0',
                    marginTop: '8px',
                    fontFamily: 'monospace',
                  }}
                >
                  {dataset.id}
                </div>

                {/* Botón eliminar */}
                <button
                  onClick={(e) => handleDelete(e, dataset.id, dataset.name)}
                  style={{
                    marginTop: '16px',
                    padding: '10px',
                    width: '100%',
                    background: '#fee2e2',
                    color: '#991b1b',
                    border: '2px solid #fca5a5',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#fecaca';
                    e.currentTarget.style.borderColor = '#f87171';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#fee2e2';
                    e.currentTarget.style.borderColor = '#fca5a5';
                  }}
                >
                  🗑️ Eliminar
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
