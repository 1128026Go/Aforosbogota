/**
 * API Client para el sistema de edición de datasets
 * Updated to use /api/editor/datasets endpoint
 */

import { API_BASE_URL } from '@/config/api';
import type {
  DatasetInfo,
  DatasetConfig,
  TrajectoryEvent,
  EventUpdate,
  EventsResponse,
  StatsResponse,
  CorrectionRule,
  ApplyRulesRequest,
  ApplyRulesResponse,
  HistoryEntry,
  CardinalPointConfig,
  EventFilters,
} from '../types/dataset-editor';

const DATASET_EDITOR_BASE_URL = `${API_BASE_URL}/api/editor/datasets`;

/**
 * Helper para hacer requests con manejo de errores
 */
async function fetchAPI<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ==================== GESTIÓN DE DATASETS ====================

/**
 * Lista todos los datasets disponibles
 */
export async function listDatasets(): Promise<{ datasets: DatasetInfo[] }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/`);
}

/**
 * Obtiene información completa de un dataset
 */
export async function getDatasetInfo(datasetId: string): Promise<{
  dataset_id: string;
  config: DatasetConfig;
  events_count: number;
}> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/info`);
}

/**
 * Obtiene la configuración de un dataset
 */
export async function getDatasetConfig(datasetId: string): Promise<DatasetConfig> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/config`);
}

/**
 * Actualiza la configuración de un dataset
 */
export async function updateDatasetConfig(
  datasetId: string,
  config: DatasetConfig
): Promise<{ message: string; config: DatasetConfig }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/config`, {
    method: 'PUT',
    body: JSON.stringify(config),
  });
}

/**
 * Inicializa la configuración de un dataset nuevo
 */
export async function initializeDatasetConfig(
  datasetId: string,
  pklFile: string
): Promise<{ message: string; config: DatasetConfig }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/config/initialize`, {
    method: 'POST',
    body: JSON.stringify({ pkl_file: pklFile }),
  });
}

// ==================== GESTIÓN DE EVENTOS ====================

/**
 * Obtiene eventos con paginación y filtros
 */
export async function getEvents(
  datasetId: string,
  filters?: EventFilters
): Promise<EventsResponse> {
  const params = new URLSearchParams();

  if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());
  if (filters?.class_name) params.append('class_name', filters.class_name);
  if (filters?.origin_cardinal) params.append('origin_cardinal', filters.origin_cardinal);
  if (filters?.mov_rilsa !== undefined) params.append('mov_rilsa', filters.mov_rilsa.toString());

  const url = `${DATASET_EDITOR_BASE_URL}/${datasetId}/events?${params.toString()}`;
  return fetchAPI(url);
}

/**
 * Obtiene un evento específico por track_id
 */
export async function getEventById(
  datasetId: string,
  trackId: string | number
): Promise<TrajectoryEvent> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/events/${trackId}`);
}

/**
 * Actualiza un evento específico
 */
export async function updateEvent(
  datasetId: string,
  trackId: string | number,
  updates: EventUpdate
): Promise<{ message: string; track_id: string | number }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/events/${trackId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

/**
 * Elimina un evento
 */
export async function deleteEvent(
  datasetId: string,
  trackId: string | number
): Promise<{ message: string; track_id: string | number }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/events/${trackId}`, {
    method: 'DELETE',
  });
}

// ==================== GESTIÓN DE REGLAS ====================

/**
 * Obtiene las reglas de corrección de un dataset
 */
export async function getRules(datasetId: string): Promise<{ rules: CorrectionRule[] }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/rules`);
}

/**
 * Crea una nueva regla de corrección
 */
export async function createRule(
  datasetId: string,
  rule: CorrectionRule
): Promise<{ message: string; rule: CorrectionRule }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/rules`, {
    method: 'POST',
    body: JSON.stringify(rule),
  });
}

/**
 * Actualiza una regla existente
 */
export async function updateRule(
  datasetId: string,
  ruleId: string,
  rule: CorrectionRule
): Promise<{ message: string; rule: CorrectionRule }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/rules/${ruleId}`, {
    method: 'PUT',
    body: JSON.stringify(rule),
  });
}

/**
 * Elimina una regla
 */
export async function deleteRule(
  datasetId: string,
  ruleId: string
): Promise<{ message: string; rule_id: string }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/rules/${ruleId}`, {
    method: 'DELETE',
  });
}

/**
 * Aplica reglas de corrección al dataset
 */
export async function applyRules(
  datasetId: string,
  request: ApplyRulesRequest
): Promise<ApplyRulesResponse> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/apply-rules`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// ==================== HISTORIAL ====================

/**
 * Obtiene el historial de cambios de un dataset
 */
export async function getHistory(datasetId: string): Promise<{
  history: HistoryEntry[];
  total: number;
}> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/history`);
}

// ==================== CONFIGURACIÓN DE PUNTOS CARDINALES ====================

/**
 * Actualiza la configuración de un punto cardinal
 */
export async function updateCardinalPoint(
  datasetId: string,
  cardinal: string,
  config: CardinalPointConfig
): Promise<{ message: string; config: CardinalPointConfig }> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/cardinal-points/${cardinal}`, {
    method: 'PUT',
    body: JSON.stringify(config),
  });
}

// ==================== ESTADÍSTICAS ====================

/**
 * Obtiene estadísticas generales del dataset
 */
export async function getDatasetStats(datasetId: string): Promise<StatsResponse> {
  return fetchAPI(`${DATASET_EDITOR_BASE_URL}/${datasetId}/stats`);
}
