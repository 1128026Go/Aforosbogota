/**
 * API client for AFOROS RILSA v3.0.2 - Complete 7-step workflow
 */
import {
  DatasetConfig,
  TrajectoryPoint,
  AccessPolygonUpdate,
  UploadResponse,
  DatasetMetadata,
  VolumesResponse,
  SpeedsResponse,
  ConflictsResponse,
  AnalysisSettings,
  ForbiddenMovement,
  ViolationsResponse,
  AccessGenerationResponse,
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
      maxSamples?: number;
    }
  ): Promise<AccessGenerationResponse> {
    const payload: Record<string, unknown> = {};

    if (options?.trajectories && options.trajectories.length > 0) {
      payload.trajectories = options.trajectories;
    }
    if (typeof options?.imageWidth === "number") {
      payload.image_width = options.imageWidth;
    }
    if (typeof options?.imageHeight === "number") {
      payload.image_height = options.imageHeight;
    }
    if (typeof options?.maxSamples === "number") {
      payload.max_samples = options.maxSamples;
    }

    const response = await fetch(
      `${API_BASE_URL}/api/v1/config/${datasetId}/generate_accesses`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: Object.keys(payload).length ? JSON.stringify(payload) : undefined,
      }
    );
    if (!response.ok) {
      const detail = await response.json().catch(() => null);
      const message = detail?.detail || response.statusText;
      throw new Error(`Failed to generate accesses: ${message}`);
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

  async getAnalysisSettings(datasetId: string): Promise<AnalysisSettings> {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/${datasetId}/analysis_settings`);
    if (!response.ok) {
      throw new Error(`Failed to load analysis settings: ${response.statusText}`);
    }
    return response.json();
  },

  async updateAnalysisSettings(datasetId: string, payload: AnalysisSettings): Promise<AnalysisSettings> {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/${datasetId}/analysis_settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Failed to update analysis settings: ${response.statusText}`);
    }
    return response.json();
  },

  async getForbiddenMovements(datasetId: string): Promise<ForbiddenMovement[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/${datasetId}/forbidden_movements`);
    if (!response.ok) {
      throw new Error(`Failed to load forbidden movements: ${response.statusText}`);
    }
    return response.json();
  },

  async updateForbiddenMovements(
    datasetId: string,
    payload: ForbiddenMovement[]
  ): Promise<ForbiddenMovement[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/${datasetId}/forbidden_movements`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Failed to update forbidden movements: ${response.statusText}`);
    }
    return response.json();
  },

  // ========== REPORTS ==========
  async getVolumes(datasetId: string): Promise<VolumesResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${datasetId}/volumes`);
    if (!response.ok) {
      throw new Error(`Failed to load volumes: ${response.statusText}`);
    }
    return response.json();
  },

  async getSpeeds(
    datasetId: string,
    options?: { fps?: number; pixelToMeter?: number }
  ): Promise<SpeedsResponse> {
    const params = new URLSearchParams();
    if (options?.fps) params.append("fps", options.fps.toString());
    if (options?.pixelToMeter) params.append("pixel_to_meter", options.pixelToMeter.toString());
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

  async getViolations(datasetId: string): Promise<ViolationsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${datasetId}/violations`);
    if (!response.ok) {
      throw new Error(`Failed to load violations: ${response.statusText}`);
    }
    return response.json();
  },

  async requestCsvReport(datasetId: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/api/v1/reports/${datasetId}/summary`);
    if (!response.ok) {
      throw new Error(`Failed to generate CSV: ${response.statusText}`);
    }
    const data = await response.json();
    return data.file_name;
  },

  async requestExcelReport(datasetId: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/api/v1/reports/${datasetId}/excel`);
    if (!response.ok) {
      throw new Error(`Failed to generate Excel: ${response.statusText}`);
    }
    const data = await response.json();
    return data.file_name;
  },

  async requestPdfReport(datasetId: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/api/v1/reports/${datasetId}/pdf`);
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
};

export default api;
