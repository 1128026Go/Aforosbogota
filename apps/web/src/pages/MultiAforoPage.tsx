/**
 * Página principal Multi-Aforo
 * Muestra los gráficos filtrados por aforo seleccionado
 */

import React from 'react';
import SelectorAforo from '../components/Header/SelectorAforo';
import CanvasPanel from '../components/MultiAforo/CanvasPanel';
import { useAforos } from '../store/aforos';

// Definición de aforos disponibles
const AFOROS_DISPONIBLES = [
  { id: 'aforo_001', label: 'GX010322 - Intersección Principal' },
  { id: 'aforo_002', label: 'GX020322 - Intersección Secundaria' },
  { id: 'aforo_003', label: 'Aforo 003' },
];

export default function MultiAforoPage() {
  const listAforos = useAforos((s) => s.listAforos);
  const aforosActivos = listAforos();

  // Filtrar solo los aforos que tienen datos
  const aforosConDatos = AFOROS_DISPONIBLES.filter((aforo) =>
    aforosActivos.some((a) => a.id === aforo.id)
  );

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
          <h1 style={{ color: 'white', fontSize: '28px', margin: '0 0 8px 0' }}>
            📊 Sistema Multi-Aforo en Vivo
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.9)', margin: 0, fontSize: '14px' }}>
            Visualización de trayectorias y conteos en tiempo real
          </p>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <SelectorAforo options={AFOROS_DISPONIBLES} />

          <a
            href="/aforos"
            style={{
              padding: '10px 20px',
              background: 'rgba(255,255,255,0.2)',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '8px',
              fontWeight: '600',
              fontSize: '14px',
              border: '2px solid rgba(255,255,255,0.3)',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.3)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
            }}
          >
            📚 Ver Biblioteca
          </a>
        </div>
      </div>

      {/* Contenido Principal */}
      <div style={{ padding: '40px' }}>
        {aforosConDatos.length === 0 ? (
          <div
            style={{
              padding: '80px',
              textAlign: 'center',
              background: 'white',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ fontSize: '64px', marginBottom: '24px' }}>🚗</div>
            <h2 style={{ fontSize: '24px', color: '#2c3e50', marginBottom: '16px' }}>
              No hay aforos con datos
            </h2>
            <p style={{ fontSize: '16px', color: '#7f8c8d', marginBottom: '32px' }}>
              Los aforos aparecerán automáticamente cuando se completen trayectorias
            </p>

            {/* Botón para ir a simulador */}
            <div style={{ marginTop: '32px' }}>
              <TestTrajectoryButton />
            </div>
          </div>
        ) : (
          <CanvasPanel aforos={aforosConDatos} />
        )}
      </div>
    </div>
  );
}

// Componente de prueba (reutilizado del main.tsx original)
function TestTrajectoryButton() {
  const [count, setCount] = React.useState(0);
  const [selectedAforo, setSelectedAforo] = React.useState('aforo_001');

  const simulateTrajectory = () => {
    import('../lib/aforoBus').then(({ aforoBus }) => {
      import('../lib/rilsa').then(({ mapRilsa }) => {
        const origins: Array<'N' | 'S' | 'E' | 'O'> = ['N', 'S', 'E', 'O'];
        const clases: Array<'car' | 'truck' | 'bus' | 'motorcycle' | 'bicycle' | 'person'> = [
          'car',
          'truck',
          'bus',
          'motorcycle',
          'bicycle',
          'person',
        ];

        const origin = origins[Math.floor(Math.random() * origins.length)];
        const dest = origins[Math.floor(Math.random() * origins.length)];
        const clase = clases[Math.floor(Math.random() * clases.length)];

        aforoBus.publish({
          aforoId: selectedAforo,
          track_id: `test-${Date.now()}-${Math.random()}`,
          clase,
          t_exit_iso: new Date().toISOString(),
          origin_cardinal: origin,
          dest_cardinal: dest,
          mov_rilsa: mapRilsa(origin, dest),
          ramal: origin,
          v_kmh_mediana: Math.random() * 60 + 20,
        });

        setCount((c) => c + 1);
        console.log(`✅ Trayectoria simulada para ${selectedAforo}: ${clase} (${origin}→${dest})`);
      });
    });
  };

  return (
    <div style={{ display: 'inline-block' }}>
      <div style={{ marginBottom: '16px' }}>
        <label
          htmlFor="test-aforo-select"
          style={{
            display: 'block',
            fontSize: '14px',
            fontWeight: '600',
            color: '#2c3e50',
            marginBottom: '8px',
          }}
        >
          Simular trayectorias para:
        </label>
        <select
          id="test-aforo-select"
          value={selectedAforo}
          onChange={(e) => setSelectedAforo(e.target.value)}
          style={{
            padding: '10px 16px',
            fontSize: '14px',
            borderRadius: '6px',
            border: '2px solid #e0e0e0',
            background: 'white',
            cursor: 'pointer',
            outline: 'none',
            minWidth: '300px',
          }}
        >
          <option value="aforo_001">GX010322 - Intersección Principal</option>
          <option value="aforo_002">GX020322 - Intersección Secundaria</option>
          <option value="aforo_003">Aforo 003</option>
        </select>
      </div>

      <button
        onClick={simulateTrajectory}
        style={{
          padding: '14px 28px',
          background: '#3498db',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontWeight: '600',
          fontSize: '15px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = '#2980b9';
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = '#3498db';
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        }}
      >
        🚗 Simular Trayectoria ({count})
      </button>
    </div>
  );
}
