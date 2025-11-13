/**
 * Selector de Aforo en el Header
 * Cambia el aforo seleccionado globalmente
 */

import React from 'react';
import { useUI } from '@/store/ui';

interface AforoOption {
  id: string;
  label: string;
}

interface SelectorAforoProps {
  options: AforoOption[];
}

export default function SelectorAforo({ options }: SelectorAforoProps) {
  const { selectedAforoId, setSelectedAforoId } = useUI();

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <label
        htmlFor="aforo-selector"
        style={{
          fontSize: '14px',
          fontWeight: '600',
          color: '#2c3e50',
        }}
      >
        Seleccionar Aforo:
      </label>
      <select
        id="aforo-selector"
        value={selectedAforoId}
        onChange={(e) => setSelectedAforoId(e.target.value as any)}
        style={{
          padding: '10px 16px',
          fontSize: '14px',
          borderRadius: '8px',
          border: '2px solid #3498db',
          background: 'white',
          color: '#2c3e50',
          cursor: 'pointer',
          outline: 'none',
          fontWeight: '600',
          minWidth: '250px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        }}
      >
        <option value="ALL">📊 Todos los Aforos</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
