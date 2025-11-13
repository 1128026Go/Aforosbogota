-- ======================================
-- Bogotá Traffic Database Indexes
-- Optimización para consultas frecuentes
-- ======================================

-- ======================================
-- Índices para tabla: simulations
-- ======================================
CREATE INDEX IF NOT EXISTS idx_simulations_status ON simulations(status);
CREATE INDEX IF NOT EXISTS idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_simulations_map_name ON simulations(map_name);
CREATE INDEX IF NOT EXISTS idx_simulations_config ON simulations USING GIN(config);

-- ======================================
-- Índices para tabla: vehicles
-- ======================================
-- Índice por simulación (consultas filtradas por simulación)
CREATE INDEX IF NOT EXISTS idx_vehicles_simulation_id ON vehicles(simulation_id);

-- Índice espacial para consultas geográficas
CREATE INDEX IF NOT EXISTS idx_vehicles_location ON vehicles USING GIST(location);

-- Índice temporal para series de tiempo
CREATE INDEX IF NOT EXISTS idx_vehicles_recorded_at ON vehicles(recorded_at DESC);

-- Índice compuesto para consultas por simulación y tiempo
CREATE INDEX IF NOT EXISTS idx_vehicles_simulation_time ON vehicles(simulation_id, recorded_at DESC);

-- Índice para búsqueda por ID de vehículo
CREATE INDEX IF NOT EXISTS idx_vehicles_vehicle_id ON vehicles(vehicle_id);

-- Índice para tipo de vehículo
CREATE INDEX IF NOT EXISTS idx_vehicles_type ON vehicles(vehicle_type);

-- Índice JSONB para metadatos
CREATE INDEX IF NOT EXISTS idx_vehicles_metadata ON vehicles USING GIN(metadata);

-- ======================================
-- Índices para tabla: snapshots_metadata
-- ======================================
CREATE INDEX IF NOT EXISTS idx_snapshots_simulation_id ON snapshots_metadata(simulation_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON snapshots_metadata(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_name ON snapshots_metadata(snapshot_name);

-- ======================================
-- Índices para tabla: traffic_lights
-- ======================================
CREATE INDEX IF NOT EXISTS idx_traffic_lights_simulation_id ON traffic_lights(simulation_id);
CREATE INDEX IF NOT EXISTS idx_traffic_lights_recorded_at ON traffic_lights(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_traffic_lights_location ON traffic_lights USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_traffic_lights_state ON traffic_lights(state);
CREATE INDEX IF NOT EXISTS idx_traffic_lights_id ON traffic_lights(traffic_light_id);

-- ======================================
-- Índices para tabla: pedestrians
-- ======================================
CREATE INDEX IF NOT EXISTS idx_pedestrians_simulation_id ON pedestrians(simulation_id);
CREATE INDEX IF NOT EXISTS idx_pedestrians_recorded_at ON pedestrians(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_pedestrians_location ON pedestrians USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_pedestrians_pedestrian_id ON pedestrians(pedestrian_id);

-- ======================================
-- Índices para tabla: collisions
-- ======================================
CREATE INDEX IF NOT EXISTS idx_collisions_simulation_id ON collisions(simulation_id);
CREATE INDEX IF NOT EXISTS idx_collisions_occurred_at ON collisions(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_collisions_location ON collisions USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_collisions_severity ON collisions(severity);

-- ======================================
-- Índices para tabla: map_data
-- ======================================
CREATE INDEX IF NOT EXISTS idx_map_data_bounds ON map_data USING GIST(bounds);
CREATE INDEX IF NOT EXISTS idx_map_data_center ON map_data USING GIST(center);

-- ======================================
-- Estadísticas y análisis
-- ======================================
-- Actualizar estadísticas para mejorar el query planner
-- Tablas de simulación (legado)
ANALYZE simulations;
ANALYZE vehicles;
ANALYZE snapshots_metadata;
ANALYZE traffic_lights;
ANALYZE pedestrians;
ANALYZE collisions;
ANALYZE map_data;

-- ======================================
-- Índices para tablas de aforo (nuevo módulo)
-- ======================================
-- Dataset base
CREATE INDEX IF NOT EXISTS idx_aforo_datasets_key ON aforo_datasets(dataset_key);
CREATE INDEX IF NOT EXISTS idx_aforo_datasets_updated_at ON aforo_datasets(updated_at DESC);

-- Accesos cardinales
CREATE INDEX IF NOT EXISTS idx_cardinal_accesses_dataset ON aforo_cardinal_accesses(dataset_id);
CREATE INDEX IF NOT EXISTS idx_cardinal_accesses_cardinal ON aforo_cardinal_accesses(cardinal_official);

-- Reglas RILSA
CREATE INDEX IF NOT EXISTS idx_rilsa_rules_dataset ON aforo_rilsa_rules(dataset_id);
CREATE INDEX IF NOT EXISTS idx_rilsa_rules_code ON aforo_rilsa_rules(rilsa_code);

-- Eventos de trayectorias (consultas por dataset, filtros por clase/origen/destino/movimiento)
CREATE INDEX IF NOT EXISTS idx_events_dataset ON aforo_trajectory_events(dataset_id);
CREATE INDEX IF NOT EXISTS idx_events_class ON aforo_trajectory_events(class);
CREATE INDEX IF NOT EXISTS idx_events_origin_cardinal ON aforo_trajectory_events(origin_cardinal);
CREATE INDEX IF NOT EXISTS idx_events_destination_cardinal ON aforo_trajectory_events(destination_cardinal);
CREATE INDEX IF NOT EXISTS idx_events_mov_rilsa ON aforo_trajectory_events(mov_rilsa);
CREATE INDEX IF NOT EXISTS idx_events_frame_entry ON aforo_trajectory_events(frame_entry);

-- Conteos agregados de movimientos
CREATE INDEX IF NOT EXISTS idx_movement_counts_dataset ON aforo_movement_counts(dataset_id);
CREATE INDEX IF NOT EXISTS idx_movement_counts_code ON aforo_movement_counts(movement_code);
CREATE INDEX IF NOT EXISTS idx_movement_counts_interval ON aforo_movement_counts(interval_start, interval_end);

-- Historial
CREATE INDEX IF NOT EXISTS idx_dataset_history_dataset ON aforo_dataset_history(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_history_action ON aforo_dataset_history(action);

-- Actualizar estadísticas nuevas
ANALYZE aforo_datasets;
ANALYZE aforo_cardinal_accesses;
ANALYZE aforo_rilsa_rules;
ANALYZE aforo_trajectory_events;
ANALYZE aforo_movement_counts;
ANALYZE aforo_dataset_history;

-- ======================================
-- Mensaje de confirmación
-- ======================================
\echo 'Indexes created successfully!'
