/**
 * Página de Detalle del Aforo
 * Con sistema de gating: Cardinals → RILSA Map → Live Aforo + Gráficas
 */

import React, { useEffect } from 'react';
import { useParams, useNavigate } from '@/main';
import { useDatasets } from '@/store/datasets';
import CardinalWizard from '@/components/Config/CardinalWizard';
import RilsaMapEditor from '@/components/Config/RilsaMapEditor';
import LiveAforoView from '@/components/Config/LiveAforoView';

export default function AforoDetailPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const { datasets, status, selectDataset, loadDatasets } = useDatasets();

  const currentDataset = datasets.find((d) => d.id === datasetId);

  useEffect(() => {
    if (!datasetId) {
      navigate('/library');
      return;
    }

    loadDatasets();
    selectDataset(datasetId);
  }, [datasetId, selectDataset, loadDatasets, navigate]);

  if (!currentDataset) {
    return (
      <div style={{ minHeight: '100vh', background: '#f5f7fa', padding: '60px 40px' }}>
        <div
          style={{
            maxWidth: '600px',
            margin: '0 auto',
            padding: '40px',
            background: 'white',
            borderRadius: '12px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '64px', marginBottom: '24px' }}>⏳</div>
          <h2 style={{ fontSize: '24px', color: '#2c3e50' }}>Cargando dataset...</h2>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div style={{ minHeight: '100vh', background: '#f5f7fa', padding: '60px 40px' }}>
        <div
          style={{
            maxWidth: '600px',
            margin: '0 auto',
            padding: '40px',
            background: 'white',
            borderRadius: '12px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '64px', marginBottom: '24px' }}>⏳</div>
          <h2 style={{ fontSize: '24px', color: '#2c3e50' }}>Verificando configuración...</h2>
        </div>
      </div>
    );
  }

  // GATING: Determinar qué vista mostrar
  const showCardinalWizard = !status.has_cardinals;
  const showRilsaEditor = status.has_cardinals && !status.has_rilsa_map;
  const showLiveAforo = status.has_cardinals && status.has_rilsa_map;

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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ color: 'white', fontSize: '28px', margin: 0 }}>
              📊 {currentDataset.name}
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.9)', margin: '8px 0 0 0', fontSize: '14px' }}>
              {currentDataset.frames.toLocaleString()} frames · {currentDataset.tracks.toLocaleString()} tracks
            </p>
          </div>

          <button
            onClick={() => navigate('/library')}
            style={{
              padding: '10px 20px',
              background: 'rgba(255,255,255,0.2)',
              color: 'white',
              border: '2px solid rgba(255,255,255,0.3)',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            ← Biblioteca
          </button>
        </div>

        {/* Progress bar */}
        <div style={{ marginTop: '20px', display: 'flex', gap: '12px', alignItems: 'center' }}>
          <StepIndicator active={showCardinalWizard} completed={status.has_cardinals} label="1. Cardinales" />
          <div style={{ flex: 1, height: '2px', background: 'rgba(255,255,255,0.3)' }} />
          <StepIndicator active={showRilsaEditor} completed={status.has_rilsa_map} label="2. RILSA" />
          <div style={{ flex: 1, height: '2px', background: 'rgba(255,255,255,0.3)' }} />
          <StepIndicator active={showLiveAforo} completed={status.intervals_ready} label="3. Aforo" />
        </div>
      </div>

      {/* Content with Gating */}
      <div style={{ padding: '40px' }}>
        {showCardinalWizard && <CardinalWizard datasetId={datasetId!} />}
        {showRilsaEditor && <RilsaMapEditor datasetId={datasetId!} />}
        {showLiveAforo && <LiveAforoView datasetId={datasetId!} />}
      </div>
    </div>
  );
}

// Componente de paso
function StepIndicator({
  active,
  completed,
  label,
}: {
  active: boolean;
  completed: boolean;
  label: string;
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          background: completed ? '#10b981' : active ? 'white' : 'rgba(255,255,255,0.3)',
          color: completed ? 'white' : active ? '#667eea' : 'rgba(255,255,255,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: '600',
          fontSize: '14px',
        }}
      >
        {completed ? '✓' : label.charAt(0)}
      </div>
      <span
        style={{
          fontSize: '14px',
          fontWeight: active ? '600' : '400',
          color: active ? 'white' : 'rgba(255,255,255,0.7)',
        }}
      >
        {label}
      </span>
    </div>
  );
}
