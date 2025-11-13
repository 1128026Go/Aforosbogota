import { useState, useEffect } from 'react';
import { getRules, createRule, updateRule, deleteRule, applyRules } from '../api/dataset-editor-api';
import type { CorrectionRule, ApplyRulesRequest } from '../types/dataset-editor';

export function useRules(datasetId: string) {
  const [rules, setRules] = useState<CorrectionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const { rules: data } = await getRules(datasetId);
      setRules(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar reglas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, [datasetId]);

  const handleCreateRule = async (rule: CorrectionRule) => {
    await createRule(datasetId, rule);
    await fetchRules();
  };

  const handleUpdateRule = async (ruleId: string, rule: CorrectionRule) => {
    await updateRule(datasetId, ruleId, rule);
    await fetchRules();
  };

  const handleDeleteRule = async (ruleId: string) => {
    await deleteRule(datasetId, ruleId);
    await fetchRules();
  };

  const handleApplyRules = async (request: ApplyRulesRequest) => {
    const result = await applyRules(datasetId, request);
    await fetchRules();
    return result;
  };

  return {
    rules,
    loading,
    error,
    refetch: fetchRules,
    createRule: handleCreateRule,
    updateRule: handleUpdateRule,
    deleteRule: handleDeleteRule,
    applyRules: handleApplyRules,
  };
}
