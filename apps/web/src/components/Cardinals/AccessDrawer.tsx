/**
 * Drawer lateral con lista de accesos marcados
 * Permite editar/eliminar accesos
 */

import React from 'react';
import type { AccessPoint } from '@/store/setup';

interface AccessDrawerProps {
  accesses: AccessPoint[];
  onEdit: (access: AccessPoint) => void;
  onDelete: (id: string) => void;
  canSave: boolean;
  onSave: () => void;
}

const CARDINAL_COLORS: Record<string, string> = {
  N: '#3b82f6',
  S: '#10b981',
  E: '#f59e0b',
  O: '#ef4444',
};

const CARDINAL_LABELS: Record<string, string> = {
  N: 'Norte',
  S: 'Sur',
  E: 'Este',
  O: 'Oeste',
};

export default function AccessDrawer({
  accesses,
  onEdit,
  onDelete,
  canSave,
  onSave,
}: AccessDrawerProps) {
  return (
    <div
      style={{
        width: '320px',
        background: 'white',
        borderLeft: '1px solid #e5e7eb',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-4px 0 12px rgba(0,0,0,0.1)',
      }}
    >
      {/* Header */}
      <div style={{ padding: '20px', borderBottom: '1px solid #e5e7eb' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#2c3e50', marginBottom: '8px' }}>
          📍 Puntos de Acceso
        </h3>
        <p style={{ fontSize: '13px', color: '#7f8c8d' }}>
          {accesses.length} acceso{accesses.length !== 1 ? 's' : ''} marcado
          {accesses.length !== 1 ? 's' : ''}
        </p>
        {accesses.length < 2 && (
          <div
            style={{
              marginTop: '12px',
              padding: '10px',
              background: '#fef3c7',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#92400e',
            }}
          >
            ⚠️ Mínimo 2 accesos requeridos
          </div>
        )}
      </div>

      {/* Lista de accesos */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {accesses.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#9ca3af' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>📍</div>
            <p style={{ fontSize: '14px' }}>
              Haz click en "Marcar Acceso" y luego en el mapa para agregar puntos
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {accesses.map((access) => (
              <div
                key={access.id}
                style={{
                  padding: '14px',
                  background: '#f9fafb',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              >
                {/* Cardinal badge */}
                <div
                  style={{
                    display: 'inline-block',
                    padding: '4px 10px',
                    background: CARDINAL_COLORS[access.cardinal_official || access.cardinal],
                    color: 'white',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: '600',
                    marginBottom: '8px',
                  }}
                >
                  {access.cardinal_official || access.cardinal} - {CARDINAL_LABELS[access.cardinal_official || access.cardinal]}
                </div>

                {/* Nombre */}
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#2c3e50', marginBottom: '12px' }}>
                  {access.display_name}
                </div>

                {/* Coords */}
                <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '12px' }}>
                  x: {Math.round(access.x)}, y: {Math.round(access.y)}
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => onEdit(access)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      background: 'white',
                      border: '1px solid #e0e0e0',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#6b7280',
                      cursor: 'pointer',
                    }}
                  >
                    ✏️ Editar
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`¿Eliminar "${access.display_name}"?`)) {
                        onDelete(access.id);
                      }
                    }}
                    style={{
                      flex: 1,
                      padding: '8px',
                      background: 'white',
                      border: '1px solid #fca5a5',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#dc2626',
                      cursor: 'pointer',
                    }}
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer con botón guardar */}
      <div style={{ padding: '16px', borderTop: '1px solid #e5e7eb' }}>
        <button
          onClick={onSave}
          disabled={!canSave}
          style={{
            width: '100%',
            padding: '14px',
            background: canSave ? '#10b981' : '#d1d5db',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: canSave ? 'pointer' : 'not-allowed',
          }}
        >
          💾 Guardar Accesos y Cardinales
        </button>
        {!canSave && (
          <p style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '8px', textAlign: 'center' }}>
            Agrega al menos 2 accesos
          </p>
        )}
      </div>
    </div>
  );
}
