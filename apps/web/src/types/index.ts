/**
 * Core type definitions for the AFOROS analysis frontend.
 */

export type Cardinal = "N" | "S" | "E" | "O";
export type MovementType = "directo" | "izquierda" | "derecha" | "retorno";

// ========== CONFIGURATION ==========
export interface AccessConfig {
  id: string;
  cardinal: Cardinal;
  polygon: [number, number][];
  centroid?: [number, number];
}

export interface RilsaRule {
  code: string;
  origin_access: Cardinal;
  dest_access: Cardinal;
  movement_type: MovementType;
  description: string;
}

export interface DatasetConfig {
  dataset_id: string;
  accesses: AccessConfig[];
  rilsa_rules: RilsaRule[];
  created_at: string;
  updated_at: string;
}

export interface AccessPolygonUpdate {
  accesses: AccessConfig[];
}

// ========== TRAJECTORIES ==========
export interface TrajectoryPoint {
  frame_id: number;
  track_id: number;
  x: number;
  y: number;
  class_id: number;
  object_type: string;
  confidence?: number;
}

// ========== DATASETS ==========
export interface DatasetMetadata {
  id: string;
  name: string;
  frames: number;
  tracks: number;
  width: number;
  height: number;
  fps?: number;
  created_at?: string;
  updated_at?: string;
  status?: "processing" | "ready" | "error";
}

export interface UploadResponse {
  dataset_id: string;
  metadata: DatasetMetadata;
  status: string;
}

// ========== ANALYSIS RESPONSES ==========
export interface VolumeRow {
  interval_start: number;
  interval_end: number;
  autos: number;
  buses: number;
  camiones: number;
  motos: number;
  bicis: number;
  peatones: number;
  total: number;
}

export interface MovementVolumeTable {
  rilsa_code: string;
  description: string;
  rows: VolumeRow[];
}

export interface VolumesResponse {
  dataset_id: string;
  interval_minutes: number;
  totals_by_interval: VolumeRow[];
  movements: MovementVolumeTable[];
}

export interface SpeedStats {
  count: number;
  mean_kmh: number;
  median_kmh: number;
  p85_kmh: number;
  min_kmh: number;
  max_kmh: number;
}

export interface MovementSpeedStats {
  rilsa_code: string;
  description: string;
  vehicle_class: string;
  stats: SpeedStats;
}

export interface SpeedsResponse {
  dataset_id: string;
  per_movement: MovementSpeedStats[];
}

export interface ConflictEvent {
  ttc_min: number;
  pet: number | null;
  time_sec: number;
  x: number;
  y: number;
  track_id_1: string;
  track_id_2: string;
  severity: number;
  pair_type: string;
}

export interface ConflictsResponse {
  dataset_id: string;
  total_conflicts: number;
  events: ConflictEvent[];
}
