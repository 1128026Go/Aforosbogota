/**
 * Asistente de Configuración de Puntos Cardinales
 * Paso 1: Definir accesos y asignar N/S/E/O
 */

import React, { useState } from 'react';
import { useDatasets } from '@/store/datasets';
import { API_BASE_URL } from '@/config/api';

interface AccessPoint {
  id: string;
  name: string;
  cardinal: 'N' | 'S' | 'E' | 'O';
  x: number;
  y: number;
}

export default function CardinalWizard({ datasetId }: { datasetId: string }) {
  const { loadStatus } = useDatasets();
  const [accessPoints, setAccessPoints] = useState<AccessPoint[]>([
    { id: 'acc_1', name: 'Acceso Norte', cardinal: 'N', x: 0, y: 0 },
    { id: 'acc_2', name: 'Acceso Sur', cardinal: 'S', x: 0, y: 0 },
    { id: 'acc_3', name: 'Acceso Este', cardinal: 'E', x: 0, y: 0 },
    { id: 'acc_4', name: 'Acceso Oeste', cardinal: 'O', x: 0, y: 0 },
  ]);
  const [saving, setSaving] = useState(false);

  const handleAddAccess = () => {
    const newId = `acc_${Date.now()}`;
    setAccessPoints([
      ...accessPoints,
      { id: newId, name: `Acceso ${accessPoints.length + 1}`, cardinal: 'N', x: 0, y: 0 },
    ]);
  };

  const handleUpdateAccess = (id: string, field: keyof AccessPoint, value: any) => {
    setAccessPoints(accessPoints.map((ap) => (ap.id === id ? { ...ap, [field]: value } : ap)));
  };

  const handleRemoveAccess = (id: string) => {
    setAccessPoints(accessPoints.filter((ap) => ap.id !== id));
  };

  const handleSave = async () => {
    setSaving(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/cardinals`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_points: accessPoints,
          metadata: { created_at: new Date().toISOString() },
        }),
      });

      if (!res.ok) throw new Error('Error guardando cardinales');

      // Recargar estado
      await loadStatus(datasetId);
    } catch (error) {
      console.error(error);
      alert('Error al guardar configuración');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: '900px',
        margin: '0 auto',
        background: 'white',
        borderRadius: '12px',
        padding: '40px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🧭</div>
        <h2 style={{ fontSize: '24px', color: '#2c3e50', marginBottom: '8px' }}>
          Paso 1: Configurar Puntos Cardinales
        </h2>
        <p style={{ fontSize: '14px', color: '#7f8c8d' }}>
          Define los accesos a la intersección y asigna su orientación cardinal (N/S/E/O)
        </p>
      </div>

      {/* Instructions */}
      <div
        style={{
          padding: '16px',
          background: '#eff6ff',
          borderLeft: '4px solid #3b82f6',
          borderRadius: '6px',
          marginBottom: '32px',
        }}
      >
        <p style={{ fontSize: '14px', color: '#1e40af', margin: 0 }}>
          💡 <strong>Instrucciones:</strong> Identifica cada acceso en el mapa de tu intersección y
          asigna su punto cardinal. Estos nombres se usarán luego para definir los movimientos RILSA.
        </p>
      </div>

      {/* Access points list */}
      <div style={{ marginBottom: '32px' }}>
        {accessPoints.map((ap, idx) => (
          <div
            key={ap.id}
            style={{
              display: 'grid',
              gridTemplateColumns: '2fr 1fr auto',
              gap: '12px',
              alignItems: 'center',
              padding: '16px',
              background: idx % 2 === 0 ? '#fafafa' : 'white',
              borderRadius: '6px',
              marginBottom: '8px',
            }}
          >
            <input
              type="text"
              value={ap.name}
              onChange={(e) => handleUpdateAccess(ap.id, 'name', e.target.value)}
              placeholder="Nombre del acceso"
              style={{
                padding: '10px',
                border: '1px solid #e0e0e0',
                borderRadius: '6px',
                fontSize: '14px',
              }}
            />

            <select
              value={ap.cardinal}
              onChange={(e) => handleUpdateAccess(ap.id, 'cardinal', e.target.value)}
              style={{
                padding: '10px',
                border: '1px solid #e0e0e0',
                borderRadius: '6px',
                fontSize: '14px',
              }}
            >
              <option value="N">Norte (N)</option>
              <option value="S">Sur (S)</option>
              <option value="E">Este (E)</option>
              <option value="O">Oeste (O)</option>
            </select>

            <button
              onClick={() => handleRemoveAccess(ap.id)}
              disabled={accessPoints.length <= 2}
              style={{
                padding: '10px 16px',
                background: accessPoints.length <= 2 ? '#e0e0e0' : '#fee',
                border: 'none',
                borderRadius: '6px',
                cursor: accessPoints.length <= 2 ? 'not-allowed' : 'pointer',
                color: accessPoints.length <= 2 ? '#999' : '#c33',
              }}
            >
              🗑️
            </button>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '12px' }}>
        <button
          onClick={handleAddAccess}
          style={{
            flex: 1,
            padding: '14px',
            background: '#f3f4f6',
            border: '1px solid #e0e0e0',
            borderRadius: '6px',
            fontSize: '15px',
            fontWeight: '600',
            cursor: 'pointer',
            color: '#6b7280',
          }}
        >
          ➕ Agregar Acceso
        </button>
        <button
          onClick={handleSave}
          disabled={saving || accessPoints.length < 2}
          style={{
            flex: 2,
            padding: '14px',
            background: saving || accessPoints.length < 2 ? '#d1d5db' : '#10b981',
            border: 'none',
            borderRadius: '6px',
            fontSize: '15px',
            fontWeight: '600',
            cursor: saving || accessPoints.length < 2 ? 'not-allowed' : 'pointer',
            color: 'white',
          }}
        >
          {saving ? '⏳ Guardando...' : '💾 Guardar y Continuar'}
        </button>
      </div>
    </div>
  );
}
