/**
 * API para gestión de configuración de datasets
 */

import { API_BASE_URL } from '../config/api';

export interface DatasetConfig {
  dataset_id: string;
  name: string;
  cardinal_config: {
    accesses: Record<string, any>;
  };
  trajectory_filters: Record<string, any>;
  correction_rules: any[];
  report_settings: Record<string, any>;
}

export interface ConfigViewResponse {
  status: string;
  dataset_id: string;
  config: DatasetConfig;
  access_coordinates: Record<string, any>;
  inferred_movements: Record<string, any>;
}

export interface GenerateConfigResponse {
  status: string;
  dataset_id: string;
  config: DatasetConfig;
  cardinals_detected: number;
  movements_inferred: number;
  message: string;
}

/**
 * Genera o actualiza dataset_config.json automáticamente
 */
export async function generateConfig(datasetId: string): Promise<GenerateConfigResponse> {
  const response = await fetch(`${API_BASE_URL}/config/generate/${datasetId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Error generando configuración: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Obtiene el dataset_config actual y sus polígonos
 */
export async function viewConfig(datasetId: string): Promise<ConfigViewResponse> {
  const response = await fetch(`${API_BASE_URL}/config/view/${datasetId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Error obteniendo configuración: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Actualiza polígonos de entrada/salida para un acceso
 */
export async function updatePolygons(
  datasetId: string,
  cardinal: string,
  entryPolygon?: number[][],
  exitPolygon?: number[][]
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/config/update-polygons/${datasetId}/${cardinal}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      entry_polygon: entryPolygon,
      exit_polygon: exitPolygon,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Error actualizando polígonos: ${response.statusText}`);
  }

  return response.json();
}




