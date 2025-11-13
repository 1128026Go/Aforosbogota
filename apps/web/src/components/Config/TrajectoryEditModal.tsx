/**
 * Panel lateral para editar/validar trayectorias individualmente
 * Permite cambiar origen, destino, categoría o marcar como descartada
 */

import { useState, useEffect } from 'react';
import { getNombreMovimiento, getEmojiMovimiento } from '@/lib/rilsa';

interface TrajectoryEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  trajectory: {
    track_id: string;
    class: string;
    origin_cardinal: string;
    dest_cardinal: string;
    mov_rilsa: number;
    positions: [number, number][];
    frame_entry: number;
    frame_exit: number;
  } | null;
  onSave: (trackId: string, newOrigin: string, newDest: string, newClass: string, discard: boolean, hideInPdf: boolean) => void;
  availableCardinals: string[];
  existingCorrection?: {
    new_origin?: string;
    new_dest?: string;
    new_class?: string;
    discard?: boolean;
    hide_in_pdf?: boolean;
  } | null;
}

const CARDINAL_NAMES: Record<string, string> = {
  N: 'Norte',
  S: 'Sur',
  E: 'Este',
  O: 'Oeste',
};

const CLASS_NAMES: Record<string, string> = {
  car: 'Auto',
  motorcycle: 'Moto',
  bus: 'Bus',
  truck: 'Camión',
  truck_c1: 'Camión C1',
  truck_c2: 'Camión C2',
  truck_c3: 'Camión C3',
  bicycle: 'Bicicleta',
  person: 'Peatón',
};

export default function TrajectoryEditModal({
  isOpen,
  onClose,
  trajectory,
  onSave,
  availableCardinals,
  existingCorrection,
}: TrajectoryEditModalProps) {
  const [newOrigin, setNewOrigin] = useState('');
  const [newDest, setNewDest] = useState('');
  const [newClass, setNewClass] = useState('');
  const [discard, setDiscard] = useState(false);
  const [hideInPdf, setHideInPdf] = useState(false);

  useEffect(() => {
    if (trajectory) {
      console.log('🎯 Modal received trajectory:', trajectory.track_id);
      console.log('📋 Existing correction:', existingCorrection);

      // Cargar valores desde corrección existente si hay, sino usar valores originales
      setNewOrigin(existingCorrection?.new_origin || trajectory.origin_cardinal);
      setNewDest(existingCorrection?.new_dest || trajectory.dest_cardinal);
      setNewClass(existingCorrection?.new_class || trajectory.class);
      setDiscard(existingCorrection?.discard || false);
      setHideInPdf(existingCorrection?.hide_in_pdf || false);
    }
  }, [trajectory, existingCorrection]);

  console.log('🔍 Modal render - isOpen:', isOpen, 'trajectory:', trajectory?.track_id);
  if (!isOpen || !trajectory) return null;

  const handleSave = () => {
    onSave(trajectory.track_id, newOrigin, newDest, newClass, discard, hideInPdf);
    onClose();
  };

  // Calcular nuevo código RILSA
  const getPreviewRilsa = () => {
    if (discard) return null;
    if (newOrigin === 'N' && newDest === 'S') return 1;
    if (newOrigin === 'S' && newDest === 'N') return 2;
    if (newOrigin === 'E' && newDest === 'O') return 3;
    if (newOrigin === 'O' && newDest === 'E') return 4;
    if (newOrigin === 'N' && newDest === 'E') return 5;
    if (newOrigin === 'S' && newDest === 'O') return 6;
    if (newOrigin === 'O' && newDest === 'N') return 7;
    if (newOrigin === 'E' && newDest === 'S') return 8;
    if (newOrigin === 'N' && newDest === 'O') return 91;
    if (newOrigin === 'S' && newDest === 'E') return 92;
    if (newOrigin === 'O' && newDest === 'S') return 93;
    if (newOrigin === 'E' && newDest === 'N') return 94;
    if (newOrigin === 'N' && newDest === 'N') return 101;
    if (newOrigin === 'S' && newDest === 'S') return 102;
    if (newOrigin === 'O' && newDest === 'O') return 103;
    if (newOrigin === 'E' && newDest === 'E') return 104;
    return null;
  };

  const previewRilsa = getPreviewRilsa();
  const hasChanges = newOrigin !== trajectory.origin_cardinal ||
                    newDest !== trajectory.dest_cardinal ||
                    newClass !== trajectory.class ||
                    discard ||
                    hideInPdf;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: '400px',
      background: 'white',
      boxShadow: '-4px 0 12px rgba(0,0,0,0.15)',
      zIndex: 1000,
      overflowY: 'auto',
      borderLeft: '1px solid #e5e7eb'
    }}>
      <div style={{ padding: '24px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#111827', margin: 0 }}>
            Editar Trayectoria
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              fontSize: '28px',
              cursor: 'pointer',
              lineHeight: 1,
              padding: 0
            }}
          >
            ×
          </button>
        </div>

        {/* Información actual */}
        <div style={{
          marginBottom: '20px',
          padding: '12px',
          background: '#f9fafb',
          borderRadius: '6px',
          border: '1px solid #e5e7eb'
        }}>
          <h3 style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
            Información Actual
          </h3>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            <p style={{ margin: '4px 0' }}><strong>ID:</strong> {trajectory.track_id}</p>
            <p style={{ margin: '4px 0' }}><strong>Clase:</strong> {CLASS_NAMES[trajectory.class] || trajectory.class}</p>
            <p style={{ margin: '4px 0' }}><strong>Origen:</strong> {CARDINAL_NAMES[trajectory.origin_cardinal]} ({trajectory.origin_cardinal})</p>
            <p style={{ margin: '4px 0' }}><strong>Destino:</strong> {CARDINAL_NAMES[trajectory.dest_cardinal]} ({trajectory.dest_cardinal})</p>
            <p style={{ margin: '4px 0' }}>
              <strong>Movimiento:</strong> {getEmojiMovimiento(trajectory.mov_rilsa)} {getNombreMovimiento(trajectory.mov_rilsa)}
            </p>
            <p style={{ margin: '4px 0' }}><strong>Puntos:</strong> {trajectory.positions.length}</p>
          </div>
        </div>

        {/* Controles */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
            Nueva Categoría
          </label>
          <select
            value={newClass}
            onChange={(e) => setNewClass(e.target.value)}
            disabled={discard}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
              background: discard ? '#f3f4f6' : 'white'
            }}
          >
            <option value="car">🚗 Auto</option>
            <option value="motorcycle">🏍️ Moto</option>
            <option value="bus">🚌 Bus</option>
            <option value="truck">🚚 Camión</option>
            <option value="truck_c1">🚛 Camión C1</option>
            <option value="truck_c2">🚛 Camión C2</option>
            <option value="truck_c3">🚛 Camión C3</option>
            <option value="bicycle">🚲 Bicicleta</option>
            <option value="person">🚶 Peatón</option>
          </select>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
            Nuevo Origen
          </label>
          <select
            value={newOrigin}
            onChange={(e) => setNewOrigin(e.target.value)}
            disabled={discard}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
              background: discard ? '#f3f4f6' : 'white'
            }}
          >
            {availableCardinals.map((card) => (
              <option key={card} value={card}>
                {CARDINAL_NAMES[card]} ({card})
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
            Nuevo Destino
          </label>
          <select
            value={newDest}
            onChange={(e) => setNewDest(e.target.value)}
            disabled={discard}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
              background: discard ? '#f3f4f6' : 'white'
            }}
          >
            {availableCardinals.map((card) => (
              <option key={card} value={card}>
                {CARDINAL_NAMES[card]} ({card})
              </option>
            ))}
          </select>
        </div>

        {/* Preview del nuevo movimiento */}
        {!discard && previewRilsa && (
          <div style={{
            padding: '12px',
            background: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: '6px',
            marginBottom: '20px'
          }}>
            <p style={{ fontSize: '13px', fontWeight: '600', color: '#1e40af', margin: 0 }}>
              Nuevo movimiento: {getEmojiMovimiento(previewRilsa)} {getNombreMovimiento(previewRilsa)} (Código {previewRilsa})
            </p>
          </div>
        )}

        {/* Opción descartar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '12px',
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '6px',
          marginBottom: '12px'
        }}>
          <input
            type="checkbox"
            id="discard"
            checked={discard}
            onChange={(e) => setDiscard(e.target.checked)}
            style={{ marginRight: '12px', width: '16px', height: '16px' }}
          />
          <label htmlFor="discard" style={{ fontSize: '13px', fontWeight: '600', color: '#991b1b', cursor: 'pointer' }}>
            Marcar como incorrecta (descartar)
          </label>
        </div>

        {/* Opción ocultar en PDF */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '12px',
          background: '#fef9f5',
          border: '1px solid #fed7aa',
          borderRadius: '6px',
          marginBottom: '20px'
        }}>
          <input
            type="checkbox"
            id="hideInPdf"
            checked={hideInPdf}
            onChange={(e) => setHideInPdf(e.target.checked)}
            style={{ marginRight: '12px', width: '16px', height: '16px' }}
          />
          <label htmlFor="hideInPdf" style={{ fontSize: '13px', fontWeight: '600', color: '#92400e', cursor: 'pointer' }}>
            📄 Ocultar en reporte PDF (no elimina, solo oculta en capturas)
          </label>
        </div>

        {/* Botones */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={onClose}
            style={{
              flex: 1,
              padding: '10px',
              background: '#f3f4f6',
              color: '#374151',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges}
            style={{
              flex: 1,
              padding: '10px',
              background: hasChanges ? '#3b82f6' : '#d1d5db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: hasChanges ? 'pointer' : 'not-allowed'
            }}
          >
            Guardar
          </button>
        </div>
      </div>
    </div>
  );
}
