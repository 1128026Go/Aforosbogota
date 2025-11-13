/**
 * Panel de Canvas con múltiples aforos
 * Filtra y renderiza solo los aforos seleccionados
 */

import React from 'react';
import { useUI } from '@/store/ui';
import TitleOverlay from './TitleOverlay';
import AforoLivePanel from '../AforoLive/AforoLivePanel';

interface AforoInfo {
  id: string;
  title: string;
}

interface CanvasPanelProps {
  aforos: AforoInfo[];
}

// Componente placeholder para el canvas (reemplazar con canvas real)
function AforoCanvas({ aforoId }: { aforoId: string }) {
  return (
    <div
      style={{
        width: '100%',
        height: '500px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontSize: '24px',
        fontWeight: 'bold',
        position: 'relative',
        boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
      }}
    >
      🗺️ Gráfico de Trayectorias - {aforoId}
      <div style={{ position: 'absolute', bottom: '20px', fontSize: '14px', opacity: 0.8 }}>
        (Canvas interactivo se integrará aquí)
      </div>
    </div>
  );
}

export default function CanvasPanel({ aforos }: CanvasPanelProps) {
  const { selectedAforoId } = useUI();

  // Filtrar aforos según selección
  const visibles =
    selectedAforoId === 'ALL' ? aforos : aforos.filter((a) => a.id === selectedAforoId);

  if (visibles.length === 0) {
    return (
      <div
        style={{
          padding: '60px',
          textAlign: 'center',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
        <div style={{ fontSize: '18px', color: '#6b7280' }}>
          Selecciona un aforo en el selector superior
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gap: '40px' }}>
      {visibles.map((aforo) => (
        <section
          key={aforo.id}
          style={{
            position: 'relative',
            background: 'white',
            borderRadius: '12px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
            overflow: 'hidden',
          }}
        >
          {/* Canvas y título en la parte superior */}
          <div style={{ position: 'relative' }}>
            <AforoCanvas aforoId={aforo.id} />
            <TitleOverlay aforoId={aforo.id} title={aforo.title} />
          </div>

          {/* Aforo en Vivo integrado DENTRO del mismo contenedor */}
          <div>
            <AforoLivePanel aforoId={aforo.id} />
          </div>
        </section>
      ))}
    </div>
  );
}
