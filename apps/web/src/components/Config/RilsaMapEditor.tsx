/**
 * Visor de Mapa RILSA Generado Automáticamente
 * Paso 2: Mostrar movimientos generados según metodología estándar
 */

import React, { useState, useEffect } from 'react';
import { useDatasets } from '@/store/datasets';
import { API_BASE_URL } from '@/config/api';

interface RilsaRuleDetailed {
  origin_id: string;
  origin_name: string;
  origin_cardinal: string;
  dest_id: string;
  dest_name: string;
  dest_cardinal: string;
  rilsa_code: number;
  description: string;
}

export default function RilsaMapEditor({ datasetId }: { datasetId: string }) {
  const { loadStatus } = useDatasets();
  const [rules, setRules] = useState<RilsaRuleDetailed[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalMovements, setTotalMovements] = useState(0);

  // Cargar mapa RILSA generado
  useEffect(() => {
    async function loadRilsaMap() {
      try {
        const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/rilsa-map`);

        if (!res.ok) {
          console.error('No hay mapa RILSA generado aún');
          setLoading(false);
          return;
        }

        const data = await res.json();

        // Cargar cardinales para obtener nombres
        const cardinalsRes = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/cardinals`);
        if (!cardinalsRes.ok) {
          setLoading(false);
          return;
        }

        const cardinalsData = await cardinalsRes.json();
        const accesses = cardinalsData.accesses || [];

        // Generar reglas detalladas para visualización
        const detailedRules: RilsaRuleDetailed[] = [];
        const rulesMap = data.rules || {};

        Object.entries(rulesMap).forEach(([key, rilsaCode]) => {
          const [originId, destId] = key.split('->');
          const originAccess = accesses.find((a: any) => a.id === originId);
          const destAccess = accesses.find((a: any) => a.id === destId);

          if (originAccess && destAccess) {
            detailedRules.push({
              origin_id: originId,
              origin_name: originAccess.name,
              origin_cardinal: originAccess.cardinal,
              dest_id: destId,
              dest_name: destAccess.name,
              dest_cardinal: destAccess.cardinal,
              rilsa_code: rilsaCode as number,
              description: getMovementDescription(originAccess.cardinal, destAccess.cardinal),
            });
          }
        });

        setRules(detailedRules);
        setTotalMovements(detailedRules.length);
      } catch (error) {
        console.error('Error cargando mapa RILSA:', error);
      } finally {
        setLoading(false);
      }
    }

    loadRilsaMap();
  }, [datasetId]);

  const getMovementDescription = (originCardinal: string, destCardinal: string): string => {
    // Movimientos directos
    if (originCardinal === 'N' && destCardinal === 'S') return 'Directo (N → S)';
    if (originCardinal === 'S' && destCardinal === 'N') return 'Directo (S → N)';
    if (originCardinal === 'O' && destCardinal === 'E') return 'Directo (O → E)';
    if (originCardinal === 'E' && destCardinal === 'O') return 'Directo (E → O)';

    // Giros izquierda
    if (originCardinal === 'N' && destCardinal === 'E') return 'Giro izquierda (N → E)';
    if (originCardinal === 'S' && destCardinal === 'O') return 'Giro izquierda (S → O)';
    if (originCardinal === 'O' && destCardinal === 'S') return 'Giro izquierda (O → S)';
    if (originCardinal === 'E' && destCardinal === 'N') return 'Giro izquierda (E → N)';

    // Giros derecha
    if (originCardinal === 'N' && destCardinal === 'O') return 'Giro derecha (N → O)';
    if (originCardinal === 'S' && destCardinal === 'E') return 'Giro derecha (S → E)';
    if (originCardinal === 'O' && destCardinal === 'N') return 'Giro derecha (O → N)';
    if (originCardinal === 'E' && destCardinal === 'S') return 'Giro derecha (E → S)';

    // U-turns
    if (originCardinal === destCardinal) return `Vuelta en U (${originCardinal})`;

    return `${originCardinal} → ${destCardinal}`;
  };

  const getCardinalColor = (cardinal: string): string => {
    const colors: Record<string, string> = {
      N: '#3b82f6', // Azul
      S: '#10b981', // Verde
      E: '#f59e0b', // Naranja
      O: '#ef4444', // Rojo
    };
    return colors[cardinal] || '#6b7280';
  };

  if (loading) {
    return (
      <div
        style={{
          maxWidth: '900px',
          margin: '0 auto',
          padding: '40px',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
        <p style={{ color: '#7f8c8d' }}>Cargando configuración...</p>
      </div>
    );
  }

  return (
    <div
      style={{
        maxWidth: '1200px',
        margin: '0 auto',
        background: 'white',
        borderRadius: '12px',
        padding: '40px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🗺️</div>
        <h2 style={{ fontSize: '24px', color: '#2c3e50', marginBottom: '8px' }}>
          Paso 2: Mapa RILSA Generado Automáticamente
        </h2>
        <p style={{ fontSize: '14px', color: '#7f8c8d' }}>
          {totalMovements} movimientos generados según metodología estándar RILSA
        </p>
      </div>

      {/* Success Info */}
      <div
        style={{
          padding: '16px',
          background: '#d1fae5',
          borderLeft: '4px solid #10b981',
          borderRadius: '6px',
          marginBottom: '32px',
        }}
      >
        <p style={{ fontSize: '14px', color: '#065f46', margin: 0 }}>
          ✓ <strong>Mapa generado automáticamente:</strong> Los códigos RILSA se asignaron según la
          metodología estándar de ingeniería de tránsito (directos 1-4, izquierdas 5-8, derechas 9, U-turns 10).
        </p>
      </div>

      {/* RILSA Reference */}
      <div style={{ marginBottom: '32px', padding: '16px', background: '#f9fafb', borderRadius: '6px' }}>
        <h3 style={{ fontSize: '14px', color: '#6b7280', marginBottom: '12px', fontWeight: '600' }}>
          Referencia Códigos RILSA:
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '12px' }}>
          <div>1-3: Giros y directos principales</div>
          <div>4-6: Movimientos secundarios</div>
          <div>7-9: Vueltas y retornos</div>
          <div>10: Otros movimientos</div>
        </div>
      </div>

      {/* Rules Table */}
      <div style={{ marginBottom: '32px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Origen</th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Cardinal</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Destino</th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Cardinal</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Tipo de Movimiento</th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Código RILSA</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule, idx) => (
              <tr
                key={`${rule.origin_id}-${rule.dest_id}`}
                style={{
                  borderBottom: '1px solid #f3f4f6',
                  background: idx % 2 === 0 ? 'white' : '#fafafa',
                }}
              >
                <td style={{ padding: '12px', fontSize: '13px' }}>{rule.origin_name}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '4px 8px',
                      background: getCardinalColor(rule.origin_cardinal),
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                    }}
                  >
                    {rule.origin_cardinal}
                  </span>
                </td>
                <td style={{ padding: '12px', fontSize: '13px' }}>→ {rule.dest_name}</td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '4px 8px',
                      background: getCardinalColor(rule.dest_cardinal),
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                    }}
                  >
                    {rule.dest_cardinal}
                  </span>
                </td>
                <td style={{ padding: '12px', color: '#6b7280', fontSize: '13px' }}>
                  {rule.description}
                </td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '6px 12px',
                      background: '#eff6ff',
                      border: '2px solid #3b82f6',
                      borderRadius: '6px',
                      fontSize: '14px',
                      fontWeight: '700',
                      color: '#1e40af',
                      minWidth: '40px',
                    }}
                  >
                    {rule.rilsa_code}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Success message */}
      <div
        style={{
          padding: '20px',
          background: '#f0fdf4',
          borderRadius: '8px',
          border: '1px solid #86efac',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '32px', marginBottom: '12px' }}>✅</div>
        <h3 style={{ fontSize: '16px', color: '#166534', marginBottom: '8px', fontWeight: '600' }}>
          Configuración RILSA Completa
        </h3>
        <p style={{ fontSize: '14px', color: '#15803d', margin: 0 }}>
          Todos los movimientos están configurados. Ahora puedes continuar al paso 3 para ver el aforo en vivo.
        </p>
      </div>
    </div>
  );
}
