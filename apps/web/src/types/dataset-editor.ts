/**
 * Tipos TypeScript para el sistema de edición de datasets
 */

export interface CardinalPointConfig {
  entry_only: boolean;
  allow_pedestrians: boolean;
  allow_vehicles: boolean;
  coordinates?: { x: number; y: number };
}

export interface CorrectionRuleCondition {
  origin_cardinal?: string;
  destination_cardinal?: string;
  class_in?: string[];
  class_not_in?: string[];
  trajectory_length?: number;
  trajectory_length_lt?: number;
  trajectory_length_gt?: number;
  mov_rilsa?: number;
  custom_expression?: string;
}

export interface CorrectionRule {
  id: string;
  name: string;
  description?: string;
  type: 'filter' | 'modify' | 'validate';
  condition: CorrectionRuleCondition;
  action: 'remove' | 'modify_field' | 'flag' | 'keep';
  field_modifications?: Record<string, any>;
  enabled: boolean;
  created_at?: string;
}

export interface DatasetConfig {
  dataset_id: string;
  created_at: string;
  last_modified: string;
  pkl_file: string;
  cardinal_points: Record<string, CardinalPointConfig>;
  correction_rules: CorrectionRule[];
  video_info?: Record<string, any>;
  intersection_name?: string;
  location?: string;
  notes?: string;
}

export interface HistoryEntry {
  timestamp: string;
  user: string;
  action: string;
  changes: Record<string, any>;
  rules_applied?: string[];
  details?: string[];
  snapshot_file?: string;
}

export interface TrajectoryEvent {
  track_id: string | number;
  class: string;
  origin_cardinal?: string;
  destination_cardinal?: string;
  mov_rilsa?: number;
  movimiento_rilsa?: string;
  color?: string;
  trajectory?: number[][];
  timestamp_start?: number;
  timestamp_end?: number;
}

export interface EventUpdate {
  class?: string;
  origin_cardinal?: string;
  destination_cardinal?: string;
  mov_rilsa?: number;
  trajectory?: number[][];
  color?: string;
}

export interface DatasetInfo {
  dataset_id: string;
  created_at?: string;
  last_modified?: string;
  pkl_file?: string;
  events_count: number;
  has_config: boolean;
  rules_count: number;
}

export interface EventsResponse {
  events: TrajectoryEvent[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface StatsResponse {
  total_events: number;
  by_class: Record<string, number>;
  by_origin: Record<string, number>;
  by_rilsa_movement: Record<string, number>;
}

export interface ApplyRulesRequest {
  rule_ids?: string[] | null;
}

export interface ApplyRulesResponse {
  events_before: number;
  events_after: number;
  removed: number;
  rules_applied: string[];
  details: string[];
}

export interface EventFilters {
  class_name?: string;
  origin_cardinal?: string;
  mov_rilsa?: number;
  track_id?: string;
  skip?: number;
  limit?: number;
}
