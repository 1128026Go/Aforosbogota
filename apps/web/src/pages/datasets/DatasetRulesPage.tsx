import React, { useState } from 'react';
import { useParams } from '../../main';
import { useRules } from '../../hooks/useRules';
import { LoadingSpinner } from '../../components/shared/LoadingSpinner';
import { Button } from '../../components/shared/Button';
import { Badge } from '../../components/shared/Badge';
import { useToast } from '../../components/shared/Toast';
import { StepNavigation } from '../../components/shared/StepNavigation';

export function DatasetRulesPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const { rules, loading, applyRules } = useRules(datasetId);
  const [applying, setApplying] = useState(false);
  const { showToast, ToastComponent } = useToast();

  const handleApplyRules = async () => {
    try {
      setApplying(true);
      const result = await applyRules({ rule_ids: null });
      showToast(`Reglas aplicadas: ${result.removed} eventos eliminados`, 'success');
    } catch (err) {
      showToast('Error al aplicar reglas', 'error');
    } finally {
      setApplying(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Navegación por pasos */}
      <StepNavigation currentStepKey="rules" datasetId={datasetId} />
      
      {ToastComponent}

      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '600', marginBottom: '8px' }}>
            Reglas de Corrección
          </h1>
          <p style={{ color: '#6b7280' }}>{datasetId}</p>
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
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              border: `2px solid ${rule.enabled ? '#10b981' : '#e5e7eb'}`,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px' }}>
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

            <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: '#6b7280' }}>
              <span>Tipo: {rule.type}</span>
              <span>Acción: {rule.action}</span>
            </div>

            <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px', fontSize: '13px' }}>
              <strong>Condiciones:</strong>
              <pre style={{ marginTop: '8px', color: '#374151', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(rule.condition, null, 2)}
              </pre>
            </div>
          </div>
        ))}
      </div>

      {rules.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px', color: '#6b7280' }}>
          <p>No hay reglas configuradas para este dataset</p>
        </div>
      )}
    </div>
  );
}
