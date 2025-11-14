/**
 * API client for AFOROS RILSA v3.0.2 - Complete 7-step workflow
 */
import {
  DatasetConfig,
  AccessConfig,
  TrajectoryPoint,
  AccessPolygonUpdate,
  UploadResponse,
  DatasetMetadata,
  VolumesResponse,
  SpeedsResponse,
  ConflictsResponse,
} from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:3004";

const api = {
  // ========== DATASETS (Step 1: Upload) ==========
  async uploadDataset(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/v1/datasets/upload`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    return response.json();
  },

  async listDatasets(): Promise<DatasetMetadata[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/datasets/list`);
    if (!response.ok) {
      throw new Error(`Failed to list datasets: ${response.statusText}`);
    }
    const data = await response.json();
    return data.datasets || [];
  },

  async getDataset(datasetId: string): Promise<DatasetMetadata> {
    const response = await fetch(`${API_BASE_URL}/api/v1/datasets/${datasetId}`);
    if (!response.ok) {
      throw new Error(`Failed to get dataset: ${response.statusText}`);
    }
    const data = await response.json();
    return data.metadata;
  },

  // ========== CONFIG (Step 2: Configure Accesses) ==========
  async viewConfig(datasetId: string): Promise<DatasetConfig> {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/view/${datasetId}`);
    if (!response.ok) {
      throw new Error(`Failed to load config: ${response.statusText}`);
    }
    return response.json();
  },

  async generateAccesses(
    datasetId: string,
    options?: {
      trajectories?: TrajectoryPoint[];
      imageWidth?: number;
      imageHeight?: number;
    }
  ): Promise<AccessConfig[]> {
    const params = new URLSearchParams();
    if (options?.imageWidth) params.append("image_width", options.imageWidth.toString());
    if (options?.imageHeight) params.append("image_height", options.imageHeight.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/v1/config/generate_accesses/${datasetId}?${params.toString()}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trajectories: options?.trajectories || [],
        }),
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to generate accesses: ${response.statusText}`);
    }
    return response.json();
  },

  async saveAccesses(
    datasetId: string,
    update: AccessPolygonUpdate
  ): Promise<DatasetConfig> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/config/save_accesses/${datasetId}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(update),
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to save accesses: ${response.statusText}`);
    }
    return response.json();
  },

  async generateRilsaRules(datasetId: string): Promise<DatasetConfig> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/config/generate_rilsa/${datasetId}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to generate RILSA rules: ${response.statusText}`);
    }
    return response.json();
  },

  // ========== VALIDATION (Step 3: Statistical Validation) ==========
  // ========== REPORTS ==========
  async getVolumes(datasetId: string, intervalMinutes = 15): Promise<VolumesResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/analysis/${datasetId}/volumes?interval_minutes=${intervalMinutes}`
    );
    if (!response.ok) {
      throw new Error(`Failed to load volumes: ${response.statusText}`);
    }
    return response.json();
  },

  async getSpeeds(
    datasetId: string,
    options?: { fps?: number; pixelToMeter?: number; minLength?: number }
  ): Promise<SpeedsResponse> {
    const params = new URLSearchParams();
    if (options?.fps) params.append("fps", options.fps.toString());
    if (options?.pixelToMeter) params.append("pixel_to_meter", options.pixelToMeter.toString());
    if (options?.minLength) params.append("min_length_m", options.minLength.toString());
    const query = params.toString();
    const url = query
      ? `${API_BASE_URL}/api/v1/analysis/${datasetId}/speeds?${query}`
      : `${API_BASE_URL}/api/v1/analysis/${datasetId}/speeds`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load speeds: ${response.statusText}`);
    }
    return response.json();
  },

  async getConflicts(
    datasetId: string,
    options?: { fps?: number; ttcThreshold?: number; distanceThreshold?: number }
  ): Promise<ConflictsResponse> {
    const params = new URLSearchParams();
    if (options?.fps) params.append("fps", options.fps.toString());
    if (options?.ttcThreshold) params.append("ttc_threshold", options.ttcThreshold.toString());
    if (options?.distanceThreshold) params.append("distance_threshold", options.distanceThreshold.toString());
    const query = params.toString();
    const url = query
      ? `${API_BASE_URL}/api/v1/analysis/${datasetId}/conflicts?${query}`
      : `${API_BASE_URL}/api/v1/analysis/${datasetId}/conflicts`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load conflicts: ${response.statusText}`);
    }
    return response.json();
  },

  async requestCsvReport(datasetId: string, intervalMinutes = 15): Promise<string> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/reports/${datasetId}/summary?interval_minutes=${intervalMinutes}`
    );
    if (!response.ok) {
      throw new Error(`Failed to generate CSV: ${response.statusText}`);
    }
    const data = await response.json();
    return data.file_name;
  },

  async requestExcelReport(datasetId: string, intervalMinutes = 15): Promise<string> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/reports/${datasetId}/excel?interval_minutes=${intervalMinutes}`
    );
    if (!response.ok) {
      throw new Error(`Failed to generate Excel: ${response.statusText}`);
    }
    const data = await response.json();
    return data.file_name;
  },

  async requestPdfReport(datasetId: string, params?: { intervalMinutes?: number; fps?: number }): Promise<string> {
    const search = new URLSearchParams();
    search.append("interval_minutes", (params?.intervalMinutes ?? 15).toString());
    if (params?.fps) search.append("fps", params.fps.toString());
    const response = await fetch(`${API_BASE_URL}/api/v1/reports/${datasetId}/pdf?${search.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to generate PDF: ${response.statusText}`);
    }
    const data = await response.json();
    return data.file_name;
  },

  async downloadReport(datasetId: string, fileName: string): Promise<Blob> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/reports/${datasetId}/download/${fileName}`
    );
    if (!response.ok) {
      throw new Error(`Failed to download report: ${response.statusText}`);
    }
    return response.blob();
  },

  // ========== HISTORY (Step 7: Audit) ==========
};

export default api;
