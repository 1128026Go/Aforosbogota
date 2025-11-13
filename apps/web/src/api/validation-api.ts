/**
 * API para validación de trayectorias
 */

import { API_BASE_URL } from '../config/api';

export interface ValidationResponse {
  status: string;
  dataset_id: string;
  statistics: {
    total: number;
    valid: number;
    invalid: number;
    incomplete_count: number;
    completion_rate: number;
    errors_by_type: Record<string, number>;
  };
  valid_count: number;
  invalid_count: number;
  incomplete_count: number;
  errors_by_type: Record<string, number>;
  validation_file: string;
  message: string;
}

export interface ValidationResults {
  dataset_id: string;
  validated_at: string;
  statistics: any;
  invalid_trajectories: any[];
  incomplete_trajectories: any[];
}

/**
 * Ejecuta las reglas de validación sobre un dataset
 */
export async function runValidation(
  datasetId: string,
  autoFix: boolean = false
): Promise<ValidationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/validation/run/${datasetId}?auto_fix=${autoFix}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Error ejecutando validación: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Obtiene resultados de validación previa
 */
export async function getValidationResults(datasetId: string): Promise<{
  status: string;
  dataset_id: string;
  results: ValidationResults;
}> {
  const response = await fetch(`${API_BASE_URL}/api/validation/results/${datasetId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Error obteniendo resultados: ${response.statusText}`);
  }

  return response.json();
}




