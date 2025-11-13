/**
 * Página de Detalle - Canvas First
 * Stepper: 1) Mapa/Accesos → 2) RILSA → 3) Aforo en Vivo
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from '@/main';
import { useDatasets } from '@/store/datasets';
import { useSetup, type AccessPoint, type CardinalsConfig } from '@/store/setup';
import TrajectoryCanvas from '@/components/Canvas/TrajectoryCanvas';
import AccessModal from '@/components/Cardinals/AccessModal';
import RilsaMapEditor from '@/components/Config/RilsaMapEditor';
import LivePlaybackView from '@/components/Config/LivePlaybackView';
import { API_BASE_URL } from '@/config/api';
import { useEvents } from '@/hooks/useEvents';
import { useRules } from '@/hooks/useRules';
import { StepNavigation } from '@/components/shared/StepNavigation';
import { getHistory } from '@/api/dataset-editor-api';
import { Modal } from '@/components/shared/Modal';
import { Button } from '@/components/shared/Button';
import { Badge } from '@/components/shared/Badge';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { useToast } from '@/components/shared/Toast';

type CanvasMode = 'select' | 'mark_access' | 'draw_polygon';

export default function AforoDetailPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const { datasets, selectDataset, loadDatasets } = useDatasets();
  const { hasCardinals, hasRilsaMap, loadStatus, loadCardinals, saveCardinals } = useSetup();

  const [currentStep, setCurrentStep] = useState(1);
  const [accesses, setAccesses] = useState<AccessPoint[]>([]);
  const [canvasMode, setCanvasMode] = useState<CanvasMode>('select');
  const [modalOpen, setModalOpen] = useState(false);
  const [pendingAccess, setPendingAccess] = useState<{ x: number; y: number } | null>(null);
  const [pendingPolygon, setPendingPolygon] = useState<{ x: number; y: number }[] | null>(null);
  const [editingAccess, setEditingAccess] = useState<AccessPoint | undefined>();
  const [loading, setLoading] = useState(true);

  const currentDataset = datasets.find((d) => d.id === datasetId);

  useEffect(() => {
    if (!datasetId) {
      navigate('/library');
      return;
    }

    const initPage = async () => {
      try {
        setLoading(true);

        // 1. Cargar lista de datasets
        await loadDatasets();

        // 2. Seleccionar dataset
        selectDataset(datasetId);

        // 3. Cargar estado de configuración
        await loadStatus(datasetId);

        // 4. Determinar step inicial
        const state = useSetup.getState();
        if (!state.hasCardinals) {
          setCurrentStep(1);
        } else if (!state.hasRilsaMap) {
          setCurrentStep(2);
        } else {
          setCurrentStep(3);
        }

        // 5. Cargar cardinales si existen
        await loadCardinals(datasetId);
        const { cardinals } = useSetup.getState();
        if (cardinals) {
          // Normalizar accesos: calcular x,y desde gate si no están definidos
          const normalizedAccesses = (cardinals.accesses || []).map(acc => {
            // Si x,y ya están definidos y son válidos, usarlos
            if (acc.x != null && acc.y != null && !isNaN(acc.x) && !isNaN(acc.y)) {
              return acc;
            }

            // Si no, calcular desde el gate
            if (acc.gate) {
              const centerX = (acc.gate.x1 + acc.gate.x2) / 2;
              const centerY = (acc.gate.y1 + acc.gate.y2) / 2;
              return { ...acc, x: centerX, y: centerY };
            }

            // Si no hay gate ni coordenadas, retornar tal cual (error se manejará después)
            return acc;
          });

          console.log('✓ Accesos normalizados:', normalizedAccesses);
          setAccesses(normalizedAccesses);
        }
      } catch (error) {
        console.error('Error initializing page:', error);
      } finally {
        setLoading(false);
      }
    };

    initPage();
  }, [datasetId]);

  // Función para cambiar de paso manualmente
  const handleStepChange = (step: number) => {
    // Permitir volver hacia atrás siempre
    if (step < currentStep) {
      setCurrentStep(step);
      return;
    }

    // Validar requisitos al avanzar
    if (step === 2 && !hasCardinals) {
      alert('Primero debes guardar los accesos y cardinales');
      return;
    }
    if (step === 3 && !hasRilsaMap) {
      alert('Primero debes configurar el mapa RILSA');
      return;
    }
    if (step === 4 && !hasRilsaMap) {
      alert('Primero debes configurar el mapa RILSA');
      return;
    }

    setCurrentStep(step);
  };

  const handleAccessClick = (x: number, y: number, polygon?: { x: number; y: number }[]) => {
    setPendingAccess({ x, y });
    setPendingPolygon(polygon || null);
    setEditingAccess(undefined);
    setModalOpen(true);
  };

  const handleAccessSave = (access: AccessPoint) => {
    if (pendingAccess) {
      // Nuevo acceso con polígono
      const newAccess: any = {
        ...access,
        x: pendingAccess.x,
        y: pendingAccess.y,
      };

      // Si hay polígono pendiente, agregarlo al nuevo acceso
      if (pendingPolygon && pendingPolygon.length >= 3) {
        newAccess.polygon = pendingPolygon;
        console.log('✓ Nuevo acceso con polígono:', newAccess);
      }

      setAccesses([...accesses, newAccess]);
      setPendingAccess(null);
      setPendingPolygon(null);

      // Volver a modo select
      setCanvasMode('select');
    } else {
      // Editar existente
      setAccesses(accesses.map((a) => (a.id === access.id ? access : a)));
    }
  };

  const handleAccessMove = (id: string, x: number, y: number) => {
    setAccesses(accesses.map((a) => (a.id === id ? { ...a, x, y } : a)));
  };

  const handleEditAccess = (access: AccessPoint) => {
    setEditingAccess(access);
    setPendingAccess(null);
    setModalOpen(true);
  };

  const handleDeleteAccess = (id: string) => {
    setAccesses(accesses.filter((a) => a.id !== id));
  };

  const handlePolygonComplete = (accessId: string, polygon: { x: number; y: number }[]) => {
    console.log('✓ Polígono completado para acceso:', accessId, polygon);
    setAccesses(accesses.map((a) =>
      a.id === accessId ? { ...a, polygon } : a
    ));
  };

  const handleSaveCardinalsConfig = async () => {
    if (!datasetId || accesses.length < 2) {
      alert('Necesitas al menos 2 accesos para guardar');
      return;
    }

    // DEBUG: Ver valores de coordenadas de cada acceso
    console.log('🔍 Validando coordenadas de accesos:');
    accesses.forEach(acc => {
      console.log(`  ${acc.cardinal_official} - ${acc.display_name}:`, {
        x: acc.x,
        y: acc.y,
        'x es NaN?': isNaN(acc.x),
        'y es NaN?': isNaN(acc.y),
        gate: acc.gate,
        polygon: (acc as any).polygon
      });
    });

    // Validar que no haya NaN en las coordenadas
    const invalidAccesses = accesses.filter(acc => {
      // Verificar coordenadas centrales
      if (isNaN(acc.x) || isNaN(acc.y)) return true;

      // Verificar coordenadas del gate si existe
      if (acc.gate) {
        if (isNaN(acc.gate.x1) || isNaN(acc.gate.y1) || isNaN(acc.gate.x2) || isNaN(acc.gate.y2)) {
          return true;
        }
      }

      // Verificar coordenadas del polígono si existe
      const polygon = (acc as any).polygon;
      if (polygon && Array.isArray(polygon)) {
        if (polygon.some(p => isNaN(p.x) || isNaN(p.y))) {
          return true;
        }
      }

      return false;
    });

    if (invalidAccesses.length > 0) {
      const accesosInvalidos = invalidAccesses.map(acc => {
        const problemas = [];
        if (isNaN(acc.x) || isNaN(acc.y)) problemas.push('coordenadas centrales');
        if (acc.gate && (isNaN(acc.gate.x1) || isNaN(acc.gate.y1) || isNaN(acc.gate.x2) || isNaN(acc.gate.y2))) {
          problemas.push('gate');
        }
        const polygon = (acc as any).polygon;
        if (polygon && Array.isArray(polygon) && polygon.some((p: any) => isNaN(p.x) || isNaN(p.y))) {
          problemas.push('polígono');
        }
        return `• ${acc.cardinal_official} - ${acc.display_name} (${problemas.join(', ')})`;
      }).join('\n');

      alert(
        `Error: Los siguientes accesos tienen coordenadas inválidas:\n\n${accesosInvalidos}\n\n` +
        `Por favor, elimina solo estos accesos y vuelve a crearlos.`
      );
      return;
    }

    // DEBUG: Ver si hay polígonos antes de guardar
    console.log('🔍 DEBUG: Accesos antes de guardar:', accesses);
    accesses.forEach(acc => {
      if ((acc as any).polygon && (acc as any).polygon.length > 0) {
        console.log(`  ✓ ${acc.cardinal_official} tiene polígono con ${(acc as any).polygon.length} puntos`);
      } else {
        console.log(`  ✗ ${acc.cardinal_official} NO tiene polígono`);
      }
    });

    // Generar gates automáticamente para accesos que no tengan
    const accessesWithGates = accesses.map(acc => {
      if (acc.gate) return acc; // Ya tiene gate, no modificar

      // Generar gate según cardinal (línea de 100px de largo)
      const GATE_LENGTH = 100;
      const cardinal = acc.cardinal_official || acc.cardinal;

      let gate;
      if (cardinal === 'N' || cardinal === 'S') {
        // Norte/Sur: gate horizontal (tráfico vertical)
        gate = {
          x1: acc.x - GATE_LENGTH / 2,
          y1: acc.y,
          x2: acc.x + GATE_LENGTH / 2,
          y2: acc.y,
        };
      } else {
        // Este/Oeste: gate vertical (tráfico horizontal)
        gate = {
          x1: acc.x,
          y1: acc.y - GATE_LENGTH / 2,
          x2: acc.x,
          y2: acc.y + GATE_LENGTH / 2,
        };
      }

      return { ...acc, gate };
    });

    console.log('✓ Guardando accesos con gates:', accessesWithGates);

    // DEBUG: Ver si los polígonos siguen en accessesWithGates
    console.log('🔍 Verificando polígonos en accessesWithGates:');
    accessesWithGates.forEach(acc => {
      if ((acc as any).polygon && (acc as any).polygon.length > 0) {
        console.log(`  ✓ ${acc.cardinal_official} - polígono presente: ${(acc as any).polygon.length} puntos`);
      } else {
        console.log(`  ✗ ${acc.cardinal_official} - SIN polígono`);
      }
    });

    const config: CardinalsConfig = {
      datasetId,
      accesses: accessesWithGates,
      updatedAt: new Date().toISOString(),
    };

    console.log('📦 Config completo a enviar:', config);

    try {
      // 1. Guardar cardinales
      console.log('⏳ Llamando a saveCardinals...');
      await saveCardinals(datasetId, config);
      console.log('✅ saveCardinals completado');

      // 2. Generar automáticamente mapa RILSA
      const rilsaRes = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/rilsa-map/generate`, {
        method: 'POST',
      });

      if (rilsaRes.ok) {
        const rilsaData = await rilsaRes.json();
        alert(
          `✓ Configuración guardada!\n\n` +
          `• Accesos y cardinales guardados\n` +
          `• ${rilsaData.total_movements} movimientos RILSA generados automáticamente\n\n` +
          `Ahora puedes continuar al paso 2 (RILSA)`
        );

        // Recargar estado y avanzar al paso 2
        await loadStatus(datasetId);
        setCurrentStep(2);
      } else {
        const errorText = await rilsaRes.text();
        console.error('Error generando RILSA:', errorText);
        alert('✓ Cardinales guardados, pero hubo un error al generar movimientos RILSA');
      }
    } catch (error) {
      console.error('Error completo:', error);
      alert(`Error al guardar configuración: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  if (loading || !currentDataset) {
    return (
      <div style={{ padding: '60px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
        <p style={{ color: '#7f8c8d' }}>Cargando dataset...</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <StepNavigation currentStepKey="live" datasetId={datasetId} />
      
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
            <h1 style={{ color: 'white', fontSize: '24px', margin: '0 0 8px 0' }}>
              📊 {currentDataset.name}
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.9)', margin: 0, fontSize: '13px' }}>
              {currentDataset.frames.toLocaleString()} frames
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

        {/* Stepper */}
        <div style={{ marginTop: '20px', display: 'flex', gap: '12px', alignItems: 'center' }}>
          <Step
            active={currentStep === 1}
            completed={hasCardinals}
            num={1}
            label="Accesos"
            onClick={() => handleStepChange(1)}
          />
          <div style={{ flex: 0.5, height: '2px', background: 'rgba(255,255,255,0.3)' }} />
          <Step
            active={currentStep === 2}
            completed={hasRilsaMap}
            num={2}
            label="RILSA"
            disabled={!hasCardinals}
            onClick={() => handleStepChange(2)}
          />
          <div style={{ flex: 0.5, height: '2px', background: 'rgba(255,255,255,0.3)' }} />
          <Step
            active={currentStep === 3}
            completed={false}
            num={3}
            label="Aforo"
            disabled={!hasRilsaMap}
            onClick={() => handleStepChange(3)}
          />
          <div style={{ flex: 0.5, height: '2px', background: 'rgba(255,255,255,0.3)' }} />
          <Step
            active={currentStep === 4}
            completed={false}
            num={4}
            label="Edición"
            disabled={!hasRilsaMap}
            onClick={() => handleStepChange(4)}
          />
        </div>
      </div>

      {/* Content Area */}
      <div style={{ padding: '40px' }}>
        {currentStep === 1 && (
          <div>
            <TrajectoryCanvas
              accesses={accesses}
              mode={canvasMode}
              onModeChange={setCanvasMode}
              onAccessClick={handleAccessClick}
              onAccessMove={handleAccessMove}
              onAccessEdit={handleEditAccess}
              onAccessDelete={handleDeleteAccess}
              onSave={handleSaveCardinalsConfig}
              onPolygonComplete={handlePolygonComplete}
              datasetId={datasetId!}
            />
          </div>
        )}

        {currentStep === 2 && hasCardinals && (
          <div style={{ padding: '40px' }}>
            <button
              onClick={() => handleStepChange(1)}
              style={{
                marginBottom: '20px',
                padding: '10px 20px',
                background: 'white',
                color: '#667eea',
                border: '2px solid #667eea',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#667eea';
                e.currentTarget.style.color = 'white';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.color = '#667eea';
              }}
            >
              ← Volver a Paso 1: Accesos
            </button>
            <RilsaMapEditor datasetId={datasetId!} />
          </div>
        )}

        {currentStep === 3 && hasRilsaMap && (
          <div style={{ padding: '40px' }}>
            <button
              onClick={() => handleStepChange(2)}
              style={{
                marginBottom: '20px',
                padding: '10px 20px',
                background: 'white',
                color: '#667eea',
                border: '2px solid #667eea',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#667eea';
                e.currentTarget.style.color = 'white';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.color = '#667eea';
              }}
            >
              ← Volver a Paso 2: RILSA
            </button>
            <LivePlaybackView datasetId={datasetId!} />
          </div>
        )}

        {currentStep === 4 && hasRilsaMap && (
          <DatasetEditorView datasetId={datasetId!} />
        )}

        {/* Gating Messages */}
        {currentStep === 2 && !hasCardinals && (
          <GateMessage icon="🧭" message="Define accesos y cardinales primero" />
        )}
        {currentStep === 3 && !hasRilsaMap && (
          <GateMessage icon="🗺️" message="Configura el mapa RILSA primero" />
        )}
        {currentStep === 4 && !hasRilsaMap && (
          <GateMessage icon="🗺️" message="Configura el mapa RILSA primero" />
        )}
      </div>

      {/* Modals */}
      <AccessModal
        isOpen={modalOpen}
        access={editingAccess}
        onSave={handleAccessSave}
        onClose={() => {
          setModalOpen(false);
          setPendingAccess(null);
          setPendingPolygon(null);
        }}
      />
    </div>
  );
}

// Componente de paso
function Step({
  active,
  completed,
  disabled,
  num,
  label,
  onClick,
}: {
  active: boolean;
  completed: boolean;
  disabled?: boolean;
  num: number;
  label: string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={disabled ? undefined : onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'transform 0.2s',
      }}
      onMouseEnter={(e) => {
        if (!disabled) e.currentTarget.style.transform = 'scale(1.05)';
      }}
      onMouseLeave={(e) => {
        if (!disabled) e.currentTarget.style.transform = 'scale(1)';
      }}
    >
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
        {completed ? '✓' : num}
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

// Mensaje de gating
function GateMessage({ icon, message }: { icon: string; message: string }) {
  return (
    <div style={{ padding: '80px', textAlign: 'center' }}>
      <div style={{ fontSize: '64px', marginBottom: '24px' }}>{icon}</div>
      <h3 style={{ fontSize: '20px', color: '#2c3e50', marginBottom: '12px' }}>
        {message}
      </h3>
      <p style={{ fontSize: '14px', color: '#7f8c8d' }}>
        Completa los pasos anteriores para continuar
      </p>
    </div>
  );
}

// Componente de edición con tabs
function DatasetEditorView({ datasetId }: { datasetId: string }) {
  const [activeTab, setActiveTab] = useState<'editor' | 'rules' | 'history'>('editor');

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      {/* Tabs */}
      <div style={{
        background: 'white',
        borderRadius: '12px 12px 0 0',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        display: 'flex',
        borderBottom: '2px solid #e5e7eb'
      }}>
        <Tab
          active={activeTab === 'editor'}
          onClick={() => setActiveTab('editor')}
          label="Editor de Eventos"
          icon="✏️"
        />
        <Tab
          active={activeTab === 'rules'}
          onClick={() => setActiveTab('rules')}
          label="Reglas de Corrección"
          icon="⚙️"
        />
        <Tab
          active={activeTab === 'history'}
          onClick={() => setActiveTab('history')}
          label="Historial"
          icon="📜"
        />
      </div>

      {/* Content */}
      <div style={{
        background: 'white',
        borderRadius: '0 0 12px 12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        minHeight: '600px'
      }}>
        {activeTab === 'editor' && <EditorTab datasetId={datasetId} />}
        {activeTab === 'rules' && <RulesTab datasetId={datasetId} />}
        {activeTab === 'history' && <HistoryTab datasetId={datasetId} />}
      </div>
    </div>
  );
}

// Componente Tab
function Tab({
  active,
  onClick,
  label,
  icon
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  icon: string;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        padding: '16px 24px',
        background: active ? 'white' : 'transparent',
        color: active ? '#667eea' : '#6b7280',
        border: 'none',
        borderBottom: active ? '3px solid #667eea' : '3px solid transparent',
        fontSize: '15px',
        fontWeight: active ? '600' : '500',
        cursor: 'pointer',
        transition: 'all 0.2s',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px'
      }}
      onMouseEnter={(e) => {
        if (!active) e.currentTarget.style.background = '#f9fafb';
      }}
      onMouseLeave={(e) => {
        if (!active) e.currentTarget.style.background = 'transparent';
      }}
    >
      <span style={{ fontSize: '18px' }}>{icon}</span>
      {label}
    </button>
  );
}

// Tab de Editor
function EditorTab({ datasetId }: { datasetId: string }) {
  const [filters, setFilters] = useState({
    skip: 0,
    limit: 50,
    class_name: undefined as string | undefined,
    origin_cardinal: undefined as string | undefined,
    mov_rilsa: undefined as number | undefined,
    track_id: undefined as string | undefined
  });
  const { events: rawEvents, total, loading, updateEvent, deleteEvent } = useEvents(datasetId, filters);
  const [editingEvent, setEditingEvent] = useState<any>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'track_id' | 'class' | 'origin_cardinal' | 'destination_cardinal' | 'mov_rilsa' | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [showFilters, setShowFilters] = useState(false);
  const { showToast, ToastComponent } = useToast();

  // Ordenar eventos localmente
  const events = React.useMemo(() => {
    if (!sortBy) return rawEvents;

    const sorted = [...rawEvents].sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];

      // Manejar valores undefined/null
      if (aVal === undefined || aVal === null) return 1;
      if (bVal === undefined || bVal === null) return -1;

      // Forzar conversión numérica para mov_rilsa
      if (sortBy === 'mov_rilsa') {
        aVal = Number(aVal);
        bVal = Number(bVal);
      }

      // Comparación numérica o string
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();

      if (sortDirection === 'asc') {
        return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
      } else {
        return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
      }
    });

    return sorted;
  }, [rawEvents, sortBy, sortDirection]);

  // Manejar clic en columna para ordenar
  const handleSort = (column: typeof sortBy) => {
    if (sortBy === column) {
      // Cambiar dirección si ya está ordenando por esta columna
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Nueva columna, comenzar con ascendente
      setSortBy(column);
      setSortDirection('asc');
    }
  };

  // Helper para actualizar filtros y resetear paginación
  const updateFilters = (newFilters: Partial<typeof filters>) => {
    setFilters({ ...filters, ...newFilters, skip: 0 });
  };

  // Helper para limpiar filtros
  const clearFilters = () => {
    setFilters({ skip: 0, limit: 50, class_name: undefined, origin_cardinal: undefined, mov_rilsa: undefined, track_id: undefined });
  };

  const handleSaveEdit = async () => {
    if (!editingEvent) return;
    try {
      await updateEvent(editingEvent.track_id, {
        class: editingEvent.class,
        origin_cardinal: editingEvent.origin_cardinal,
        destination_cardinal: editingEvent.destination_cardinal,
      });
      showToast('Evento actualizado correctamente', 'success');
      setEditingEvent(null);
    } catch (err) {
      showToast('Error al actualizar evento', 'error');
    }
  };

  const handleDelete = async (trackId: string | number) => {
    try {
      await deleteEvent(trackId);
      showToast('Evento eliminado correctamente', 'success');
      setDeleteConfirm(null);
    } catch (err) {
      showToast('Error al eliminar evento', 'error');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div style={{ padding: '32px' }}>
      {ToastComponent}

      <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px', color: '#111827' }}>
            Editor de Eventos
          </h2>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>
            Total de eventos: <strong>{total}</strong>
          </p>
        </div>

        {/* Botón de filtros */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {(filters.track_id || filters.class_name || filters.origin_cardinal || filters.mov_rilsa) && (
            <div style={{ backgroundColor: '#3b82f6', color: 'white', padding: '4px 8px', borderRadius: '4px' }}>
              <Badge>
                {[filters.track_id, filters.class_name, filters.origin_cardinal, filters.mov_rilsa].filter(Boolean).length} filtro(s)
              </Badge>
            </div>
          )}
          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowFilters(!showFilters)}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            🔍 Filtros {showFilters ? '▲' : '▼'}
          </Button>
        </div>
      </div>

      {/* Panel de Filtros Desplegable */}
      {showFilters && (
        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          marginBottom: '24px',
          border: '1px solid #e5e7eb',
          animation: 'slideDown 0.2s ease-out'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#374151' }}>Filtrar eventos</h3>
            <Button size="sm" variant="secondary" onClick={clearFilters}>
              Limpiar filtros
            </Button>
          </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {/* Filtro por Track ID */}
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: '500', color: '#374151' }}>
              Track ID
            </label>
            <input
              type="text"
              placeholder="Buscar track..."
              value={filters.track_id || ''}
              onChange={(e) => updateFilters({ track_id: e.target.value || undefined })}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '14px'
              }}
            />
          </div>

          {/* Filtro por Clase */}
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: '500', color: '#374151' }}>
              Clase
            </label>
            <select
              value={filters.class_name || ''}
              onChange={(e) => updateFilters({ class_name: e.target.value || undefined })}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '14px'
              }}
            >
              <option value="">Todas</option>
              <option value="car">Car</option>
              <option value="motorcycle">Motorcycle</option>
              <option value="truck">Truck</option>
              <option value="bus">Bus</option>
              <option value="bicycle">Bicycle</option>
              <option value="person">Person</option>
            </select>
          </div>

          {/* Filtro por Origen */}
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: '500', color: '#374151' }}>
              Origen
            </label>
            <select
              value={filters.origin_cardinal || ''}
              onChange={(e) => updateFilters({ origin_cardinal: e.target.value || undefined })}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '14px'
              }}
            >
              <option value="">Todos</option>
              <option value="N">Norte (N)</option>
              <option value="S">Sur (S)</option>
              <option value="E">Este (E)</option>
              <option value="O">Oeste (O)</option>
            </select>
          </div>

          {/* Filtro por Movimiento RILSA */}
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: '500', color: '#374151' }}>
              Mov. RILSA
            </label>
            <input
              type="number"
              placeholder="Ej: 1, 2, 3..."
              value={filters.mov_rilsa || ''}
              onChange={(e) => updateFilters({ mov_rilsa: e.target.value ? parseInt(e.target.value) : undefined })}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '14px'
              }}
            />
          </div>
        </div>

          {/* Indicador de filtros activos */}
          {(filters.track_id || filters.class_name || filters.origin_cardinal || filters.mov_rilsa) && (
            <div style={{ marginTop: '12px', fontSize: '13px', color: '#6b7280' }}>
              Filtros activos: {[
                filters.track_id && `Track ID: "${filters.track_id}"`,
                filters.class_name && `Clase: ${filters.class_name}`,
                filters.origin_cardinal && `Origen: ${filters.origin_cardinal}`,
                filters.mov_rilsa && `RILSA: ${filters.mov_rilsa}`
              ].filter(Boolean).join(', ')}
            </div>
          )}
        </div>
      )}

      {/* Tabla */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
            <tr>
              <th
                onClick={() => handleSort('track_id')}
                style={{
                  padding: '12px 16px',
                  textAlign: 'left',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#374151',
                  cursor: 'pointer',
                  userSelect: 'none',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Track ID
                  {sortBy === 'track_id' && (
                    <span style={{ fontSize: '10px' }}>{sortDirection === 'asc' ? '▲' : '▼'}</span>
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort('class')}
                style={{
                  padding: '12px 16px',
                  textAlign: 'left',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#374151',
                  cursor: 'pointer',
                  userSelect: 'none',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Clase
                  {sortBy === 'class' && (
                    <span style={{ fontSize: '10px' }}>{sortDirection === 'asc' ? '▲' : '▼'}</span>
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort('origin_cardinal')}
                style={{
                  padding: '12px 16px',
                  textAlign: 'left',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#374151',
                  cursor: 'pointer',
                  userSelect: 'none',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Origen
                  {sortBy === 'origin_cardinal' && (
                    <span style={{ fontSize: '10px' }}>{sortDirection === 'asc' ? '▲' : '▼'}</span>
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort('destination_cardinal')}
                style={{
                  padding: '12px 16px',
                  textAlign: 'left',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#374151',
                  cursor: 'pointer',
                  userSelect: 'none',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Destino
                  {sortBy === 'destination_cardinal' && (
                    <span style={{ fontSize: '10px' }}>{sortDirection === 'asc' ? '▲' : '▼'}</span>
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort('mov_rilsa')}
                style={{
                  padding: '12px 16px',
                  textAlign: 'left',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#374151',
                  cursor: 'pointer',
                  userSelect: 'none',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Movimiento RILSA
                  {sortBy === 'mov_rilsa' && (
                    <span style={{ fontSize: '10px' }}>{sortDirection === 'asc' ? '▲' : '▼'}</span>
                  )}
                </div>
              </th>
              <th style={{ padding: '12px 16px', textAlign: 'right', fontSize: '13px', fontWeight: '600', color: '#374151' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event, idx) => (
              <tr key={event.track_id} style={{
                borderBottom: '1px solid #e5e7eb',
                background: idx % 2 === 0 ? 'white' : '#fafbfc'
              }}>
                <td style={{ padding: '12px 16px', color: '#374151', fontWeight: '500' }}>{event.track_id}</td>
                <td style={{ padding: '12px 16px' }}>
                  <Badge>{event.class}</Badge>
                </td>
                <td style={{ padding: '12px 16px', color: '#374151' }}>{event.origin_cardinal || '-'}</td>
                <td style={{ padding: '12px 16px', color: '#374151' }}>{event.destination_cardinal || '-'}</td>
                <td style={{ padding: '12px 16px', color: '#374151' }}>{event.movimiento_rilsa || '-'}</td>
                <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    <Button size="sm" variant="secondary" onClick={() => setEditingEvent(event)}>
                      Editar
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => setDeleteConfirm(String(event.track_id))}>
                      Eliminar
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      <div style={{
        padding: '20px 0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderTop: '1px solid #e5e7eb',
        marginTop: '16px'
      }}>
        <span style={{ color: '#6b7280', fontSize: '14px' }}>
          Mostrando {filters.skip + 1} - {Math.min(filters.skip + filters.limit, total)} de {total}
        </span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            size="sm"
            variant="secondary"
            disabled={filters.skip === 0}
            onClick={() => setFilters({ ...filters, skip: Math.max(0, filters.skip - filters.limit) })}
          >
            ← Anterior
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={filters.skip + filters.limit >= total}
            onClick={() => setFilters({ ...filters, skip: filters.skip + filters.limit })}
          >
            Siguiente →
          </Button>
        </div>
      </div>

      {/* Modal de edición */}
      {editingEvent && (
        <Modal
          isOpen={true}
          onClose={() => setEditingEvent(null)}
          title="Editar Evento"
          footer={
            <>
              <Button variant="secondary" onClick={() => setEditingEvent(null)}>Cancelar</Button>
              <Button variant="primary" onClick={handleSaveEdit}>Guardar</Button>
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '14px', color: '#374151' }}>
                Clase:
              </label>
              <select
                value={editingEvent.class}
                onChange={(e) => setEditingEvent({ ...editingEvent, class: e.target.value })}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px',
                  color: '#374151'
                }}
              >
                <option value="car">car</option>
                <option value="motorcycle">motorcycle</option>
                <option value="truck">truck</option>
                <option value="bus">bus</option>
                <option value="bicycle">bicycle</option>
                <option value="person">person</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '14px', color: '#374151' }}>
                Origen:
              </label>
              <select
                value={editingEvent.origin_cardinal || ''}
                onChange={(e) => setEditingEvent({ ...editingEvent, origin_cardinal: e.target.value })}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px',
                  color: '#374151'
                }}
              >
                <option value="">Seleccionar...</option>
                <option value="N">Norte (N)</option>
                <option value="S">Sur (S)</option>
                <option value="E">Este (E)</option>
                <option value="O">Oeste (O)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '14px', color: '#374151' }}>
                Destino:
              </label>
              <select
                value={editingEvent.destination_cardinal || ''}
                onChange={(e) => setEditingEvent({ ...editingEvent, destination_cardinal: e.target.value })}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px',
                  color: '#374151'
                }}
              >
                <option value="">Seleccionar...</option>
                <option value="N">Norte (N)</option>
                <option value="S">Sur (S)</option>
                <option value="E">Este (E)</option>
                <option value="O">Oeste (O)</option>
              </select>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal de confirmación de eliminación */}
      {deleteConfirm !== null && (
        <Modal
          isOpen={true}
          onClose={() => setDeleteConfirm(null)}
          title="Confirmar Eliminación"
          size="sm"
          footer={
            <>
              <Button variant="secondary" onClick={() => setDeleteConfirm(null)}>Cancelar</Button>
              <Button variant="danger" onClick={() => handleDelete(deleteConfirm)}>Eliminar</Button>
            </>
          }
        >
          <p style={{ color: '#374151', marginBottom: '12px' }}>
            ¿Estás seguro de que deseas eliminar el evento con Track ID <strong>{deleteConfirm}</strong>?
          </p>
          <p style={{ color: '#dc2626', fontSize: '14px' }}>
            Esta acción no se puede deshacer.
          </p>
        </Modal>
      )}
    </div>
  );
}

// Tab de Reglas
function RulesTab({ datasetId }: { datasetId: string }) {
  const { rules, loading, applyRules } = useRules(datasetId);
  const [applying, setApplying] = useState(false);
  const { showToast, ToastComponent } = useToast();

  const handleApplyRules = async () => {
    try {
      setApplying(true);
      const result = await applyRules({ rule_ids: null });
      showToast(`Reglas aplicadas exitosamente: ${result.removed} eventos eliminados`, 'success');
    } catch (err) {
      showToast('Error al aplicar reglas', 'error');
    } finally {
      setApplying(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div style={{ padding: '32px' }}>
      {ToastComponent}

      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px', color: '#111827' }}>
            Reglas de Corrección
          </h2>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>
            Gestiona las reglas automáticas de limpieza y corrección de datos
          </p>
        </div>
        <Button
          variant="primary"
          onClick={handleApplyRules}
          disabled={applying || rules.length === 0}
        >
          {applying ? 'Aplicando...' : 'Aplicar Reglas Activas'}
        </Button>
      </div>

      {/* Lista de reglas */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {rules.map((rule) => (
          <div
            key={rule.id}
            style={{
              backgroundColor: '#fafbfc',
              borderRadius: '12px',
              padding: '24px',
              border: `2px solid ${rule.enabled ? '#10b981' : '#e5e7eb'}`,
              transition: 'all 0.2s'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '6px', color: '#111827' }}>
                  {rule.name}
                </h3>
                {rule.description && (
                  <p style={{ fontSize: '14px', color: '#6b7280' }}>{rule.description}</p>
                )}
              </div>
              <Badge variant={rule.enabled ? 'success' : 'default'}>
                {rule.enabled ? 'Activa' : 'Inactiva'}
              </Badge>
            </div>

            <div style={{ display: 'flex', gap: '20px', fontSize: '13px', color: '#6b7280', marginBottom: '16px' }}>
              <span><strong>Tipo:</strong> {rule.type}</span>
              <span><strong>Acción:</strong> {rule.action}</span>
            </div>

            <div style={{
              padding: '16px',
              backgroundColor: 'white',
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              fontSize: '13px'
            }}>
              <strong style={{ color: '#374151', marginBottom: '8px', display: 'block' }}>Condiciones:</strong>
              <pre style={{
                marginTop: '8px',
                color: '#4b5563',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                fontSize: '12px',
                lineHeight: '1.6'
              }}>
                {JSON.stringify(rule.condition, null, 2)}
              </pre>
            </div>
          </div>
        ))}
      </div>

      {rules.length === 0 && (
        <div style={{ textAlign: 'center', padding: '80px 20px', color: '#9ca3af' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚙️</div>
          <p style={{ fontSize: '16px' }}>No hay reglas configuradas para este dataset</p>
        </div>
      )}
    </div>
  );
}

// Tab de Historial
function HistoryTab({ datasetId }: { datasetId: string }) {
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
    <div style={{ padding: '32px' }}>
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px', color: '#111827' }}>
          Historial de Cambios
        </h2>
        <p style={{ color: '#6b7280', fontSize: '14px' }}>
          Registro completo de todas las modificaciones realizadas
        </p>
      </div>

      {/* Timeline */}
      <div style={{ position: 'relative', paddingLeft: '48px' }}>
        {/* Línea vertical */}
        <div style={{
          position: 'absolute',
          left: '19px',
          top: 0,
          bottom: 0,
          width: '3px',
          background: 'linear-gradient(180deg, #667eea 0%, #e5e7eb 100%)',
        }} />

        {history.map((entry, idx) => (
          <div key={idx} style={{ position: 'relative', marginBottom: '32px' }}>
            {/* Punto en la línea */}
            <div style={{
              position: 'absolute',
              left: '-37px',
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              backgroundColor: '#667eea',
              border: '4px solid white',
              boxShadow: '0 0 0 3px #667eea',
            }} />

            {/* Contenido */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '24px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#111827' }}>
                    {entry.action}
                  </h3>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>
                    {new Date(entry.timestamp).toLocaleString('es-ES', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>
                <p style={{ fontSize: '13px', color: '#6b7280', marginTop: '6px' }}>
                  Por: <strong>{entry.user}</strong>
                </p>
              </div>

              {entry.details && entry.details.length > 0 && (
                <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
                  <strong style={{ fontSize: '14px', color: '#374151', display: 'block', marginBottom: '8px' }}>
                    Detalles:
                  </strong>
                  <ul style={{ marginTop: '8px', paddingLeft: '20px', color: '#6b7280', fontSize: '13px', lineHeight: '1.8' }}>
                    {entry.details.map((detail: string, i: number) => (
                      <li key={i}>{detail}</li>
                    ))}
                  </ul>
                </div>
              )}

              {entry.rules_applied && entry.rules_applied.length > 0 && (
                <div style={{ marginTop: '16px' }}>
                  <strong style={{ fontSize: '14px', color: '#374151', display: 'block', marginBottom: '10px' }}>
                    Reglas aplicadas:
                  </strong>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {entry.rules_applied.map((ruleId: string, i: number) => (
                      <span
                        key={i}
                        style={{
                          backgroundColor: '#dbeafe',
                          color: '#1e40af',
                          padding: '6px 14px',
                          borderRadius: '20px',
                          fontSize: '12px',
                          fontWeight: '500'
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
        <div style={{ textAlign: 'center', padding: '80px 20px', color: '#9ca3af' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📜</div>
          <p style={{ fontSize: '16px' }}>No hay cambios registrados aún</p>
        </div>
      )}
    </div>
  );
}
