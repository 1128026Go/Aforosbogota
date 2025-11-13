/**
 * API para generación de reportes RILSA
 */

import { API_BASE_URL } from '../config/api';

export interface RilsaReportResponse {
  status: string;
  dataset_id: string;
  report: {
    executive_summary: any;
    statistics: {
      total_trajectories: number;
      total_vehicles: number;
      movements_detected: number;
    };
  };
  files_generated: string[];
  csv_files?: string[];
  download_urls?: string[];
  generated_at: string;
}

/**
 * Genera reporte RILSA completo
 */
export async function generateRilsaReport(
  datasetId: string,
  format: 'json' | 'csv' = 'json',
  includeDiagrams: boolean = true
): Promise<RilsaReportResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/rilsa/report/${datasetId}?format=${format}&include_diagrams=${includeDiagrams}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Error generando reporte: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Descarga un archivo de reporte
 */
export function getReportDownloadUrl(datasetId: string, filename: string): string {
  return `${API_BASE_URL}/api/files/${datasetId}/reports/${filename}`;
}

/**
 * Descarga un archivo de reporte directamente
 */
export async function downloadReportFile(datasetId: string, filename: string): Promise<Blob> {
  const response = await fetch(getReportDownloadUrl(datasetId, filename));

  if (!response.ok) {
    throw new Error(`Error descargando archivo: ${response.statusText}`);
  }

  return response.blob();
}




