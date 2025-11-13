/**
 * Modal para configurar un acceso (nombre + cardinal)
 * Se abre al hacer click en el canvas en modo "Marcar Acceso"
 */

import React, { useState, useEffect } from 'react';
import type { AccessPoint, Cardinal } from '@/store/setup';

interface AccessModalProps {
  isOpen: boolean;
  access?: AccessPoint; // undefined = nuevo, defined = editar
  onSave: (access: AccessPoint) => void;
  onClose: () => void;
}

export default function AccessModal({ isOpen, access, onSave, onClose }: AccessModalProps) {
  const [name, setName] = useState('');
  const [cardinal, setCardinal] = useState<Cardinal>('N');

  useEffect(() => {
    if (access) {
      setName(access.display_name);
      setCardinal(access.cardinal_official || access.cardinal);
    } else {
      setName('');
      setCardinal('N');
    }
  }, [access, isOpen]);

  const handleSave = () => {
    if (!name.trim()) {
      alert('Debe ingresar un nombre para el acceso');
      return;
    }

    const savedAccess: AccessPoint = {
      id: access?.id || `access_${Date.now()}`,
      display_name: name.trim(),
      cardinal: cardinal, // Mantener compatibilidad legacy
      cardinal_official: cardinal, // Nuevo campo oficial
      x: access?.x || 0,
      y: access?.y || 0,
      gate: access?.gate, // Preservar gate si existe
    };

    onSave(savedAccess);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Modal */}
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            background: 'white',
            borderRadius: '12px',
            padding: '32px',
            maxWidth: '480px',
            width: '90%',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          }}
        >
          <h3 style={{ fontSize: '20px', color: '#2c3e50', marginBottom: '8px' }}>
            {access ? '✏️ Editar Acceso' : '📍 Nuevo Acceso'}
          </h3>
          <p style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '24px' }}>
            Configura el nombre y orientación cardinal de este punto de acceso
          </p>

          {/* Nombre */}
          <div style={{ marginBottom: '20px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '14px',
                fontWeight: '600',
                color: '#2c3e50',
                marginBottom: '8px',
              }}
            >
              Nombre del Acceso
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ej: Acceso Norte, Calle 72, etc."
              autoFocus
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #e0e0e0',
                borderRadius: '6px',
                fontSize: '14px',
                outline: 'none',
              }}
              onFocus={(e) => (e.currentTarget.style.borderColor = '#667eea')}
              onBlur={(e) => (e.currentTarget.style.borderColor = '#e0e0e0')}
            />
          </div>

          {/* Cardinal */}
          <div style={{ marginBottom: '24px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '14px',
                fontWeight: '600',
                color: '#2c3e50',
                marginBottom: '12px',
              }}
            >
              Orientación Cardinal
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
              {(['N', 'S', 'E', 'O'] as Cardinal[]).map((c) => (
                <button
                  key={c}
                  onClick={() => setCardinal(c)}
                  style={{
                    padding: '14px',
                    background: cardinal === c ? '#667eea' : 'white',
                    color: cardinal === c ? 'white' : '#6b7280',
                    border: `2px solid ${cardinal === c ? '#667eea' : '#e0e0e0'}`,
                    borderRadius: '8px',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  {c}
                </button>
              ))}
            </div>
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#7f8c8d' }}>
              N = Norte, S = Sur, E = Este, O = Oeste
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={onClose}
              style={{
                flex: 1,
                padding: '12px',
                background: '#f3f4f6',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#6b7280',
                cursor: 'pointer',
              }}
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              style={{
                flex: 1,
                padding: '12px',
                background: '#667eea',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                color: 'white',
                cursor: 'pointer',
              }}
            >
              {access ? 'Actualizar' : 'Guardar'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
