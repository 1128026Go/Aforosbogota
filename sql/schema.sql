-- ======================================
-- Bogotá Traffic Database Schema
-- ======================================

-- Habilitar extensiones PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- ======================================
-- Tabla: simulations
-- Registro de simulaciones ejecutadas
-- ======================================
CREATE TABLE IF NOT EXISTS simulations (
    id SERIAL PRIMARY KEY,
    simulation_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'paused')),
    config JSONB,
    map_name VARCHAR(255),
    weather_config JSONB,
    total_vehicles INTEGER DEFAULT 0,
    total_snapshots INTEGER DEFAULT 0,
    metadata JSONB,
    error_message TEXT
);

-- ======================================
-- Tabla: vehicles
-- Datos de vehículos en simulación
-- ======================================
CREATE TABLE IF NOT EXISTS vehicles (
    id BIGSERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    vehicle_id VARCHAR(100) NOT NULL,
    actor_id INTEGER,
    vehicle_type VARCHAR(50),
    recorded_at TIMESTAMPTZ NOT NULL,
    location GEOMETRY(PointZ, 4326) NOT NULL,
    velocity FLOAT,
    acceleration FLOAT,
    angular_velocity JSONB,
    heading FLOAT,
    is_at_traffic_light BOOLEAN DEFAULT FALSE,
    traffic_light_state VARCHAR(20),
    metadata JSONB
);

-- ======================================
-- Tabla: snapshots_metadata
-- Metadatos de archivos PKL generados
-- ======================================
CREATE TABLE IF NOT EXISTS snapshots_metadata (
    id SERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    snapshot_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    num_vehicles INTEGER,
    num_pedestrians INTEGER,
    simulation_timestamp FLOAT,
    checksum VARCHAR(64),
    metadata JSONB
);

-- ======================================
-- Tabla: traffic_lights
-- Estados de semáforos en la simulación
-- ======================================
CREATE TABLE IF NOT EXISTS traffic_lights (
    id BIGSERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    traffic_light_id VARCHAR(100) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    location GEOMETRY(Point, 4326),
    state VARCHAR(20) CHECK (state IN ('Green', 'Yellow', 'Red', 'Off', 'Unknown')),
    elapsed_time FLOAT,
    metadata JSONB
);

-- ======================================
-- Tabla: pedestrians
-- Datos de peatones en simulación
-- ======================================
CREATE TABLE IF NOT EXISTS pedestrians (
    id BIGSERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    pedestrian_id VARCHAR(100) NOT NULL,
    actor_id INTEGER,
    recorded_at TIMESTAMPTZ NOT NULL,
    location GEOMETRY(PointZ, 4326) NOT NULL,
    velocity FLOAT,
    metadata JSONB
);

-- ======================================
-- Tabla: collisions
-- Registro de colisiones detectadas
-- ======================================
CREATE TABLE IF NOT EXISTS collisions (
    id SERIAL PRIMARY KEY,
    simulation_id INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    occurred_at TIMESTAMPTZ NOT NULL,
    actor_a_id INTEGER,
    actor_b_id INTEGER,
    actor_a_type VARCHAR(50),
    actor_b_type VARCHAR(50),
    location GEOMETRY(Point, 4326),
    severity VARCHAR(20),
    impulse_magnitude FLOAT,
    metadata JSONB
);

-- ======================================
-- Tabla: map_data
-- Información geográfica de mapas CARLA
-- ======================================
CREATE TABLE IF NOT EXISTS map_data (
    id SERIAL PRIMARY KEY,
    map_name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    bounds GEOMETRY(Polygon, 4326),
    center GEOMETRY(Point, 4326),
    metadata JSONB
);

-- ======================================
-- Comentarios descriptivos
-- ======================================
COMMENT ON TABLE simulations IS 'Registro de todas las simulaciones ejecutadas';
COMMENT ON TABLE vehicles IS 'Trayectorias y estados de vehículos durante simulaciones';
COMMENT ON TABLE snapshots_metadata IS 'Metadatos de archivos PKL para recuperación rápida';
COMMENT ON TABLE traffic_lights IS 'Estados históricos de semáforos';
COMMENT ON TABLE pedestrians IS 'Datos de peatones en simulaciones';
COMMENT ON TABLE collisions IS 'Registro de eventos de colisión';
COMMENT ON TABLE map_data IS 'Información geográfica de mapas utilizados';

-- ======================================
-- Sección: Aforo en Vivo (Datasets reales)
-- ======================================

CREATE TABLE IF NOT EXISTS aforo_datasets (
    id SERIAL PRIMARY KEY,
    dataset_key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    frames INTEGER,
    tracks INTEGER,
    metadata JSONB
);

COMMENT ON TABLE aforo_datasets IS 'Datasets de aforo integrados (ej: dataset_f8144347)';

CREATE TABLE IF NOT EXISTS aforo_cardinal_accesses (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES aforo_datasets(id) ON DELETE CASCADE,
    access_id VARCHAR(128) NOT NULL,
    display_name VARCHAR(255),
    cardinal VARCHAR(8) NOT NULL,
    cardinal_official VARCHAR(8) NOT NULL,
    x NUMERIC,
    y NUMERIC,
    gate JSONB,
    polygon JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (dataset_id, access_id)
);

COMMENT ON TABLE aforo_cardinal_accesses IS 'Accesos cardinales configurados para cada dataset de aforo';

CREATE TABLE IF NOT EXISTS aforo_rilsa_rules (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES aforo_datasets(id) ON DELETE CASCADE,
    origin_access VARCHAR(128) NOT NULL,
    dest_access VARCHAR(128) NOT NULL,
    rilsa_code INTEGER NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (dataset_id, origin_access, dest_access)
);

COMMENT ON TABLE aforo_rilsa_rules IS 'Mapa RILSA generado por dataset (origen/destino -> código)';

CREATE TABLE IF NOT EXISTS aforo_trajectory_events (
    id BIGSERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES aforo_datasets(id) ON DELETE CASCADE,
    track_id VARCHAR(128) NOT NULL,
    class VARCHAR(64),
    origin_access VARCHAR(128),
    dest_access VARCHAR(128),
    origin_cardinal VARCHAR(8),
    destination_cardinal VARCHAR(8),
    mov_rilsa INTEGER,
    frame_entry INTEGER,
    frame_exit INTEGER,
    timestamp_entry TIMESTAMPTZ,
    timestamp_exit TIMESTAMPTZ,
    confidence DOUBLE PRECISION,
    hide_in_pdf BOOLEAN DEFAULT FALSE,
    discarded BOOLEAN DEFAULT FALSE,
    positions JSONB,
    extra JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (dataset_id, track_id)
);

COMMENT ON TABLE aforo_trajectory_events IS 'Trayectorias completas con metadatos de origen/destino y RILSA';

CREATE TABLE IF NOT EXISTS aforo_trajectory_event_revisions (
    id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES aforo_trajectory_events(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    changes JSONB NOT NULL,
    changed_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (event_id, version)
);

COMMENT ON TABLE aforo_trajectory_event_revisions IS 'Historial de correcciones aplicadas a cada trayectoria';

CREATE TABLE IF NOT EXISTS aforo_movement_counts (
    id BIGSERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES aforo_datasets(id) ON DELETE CASCADE,
    movement_code INTEGER NOT NULL,
    interval_start TIMESTAMPTZ NOT NULL,
    interval_end TIMESTAMPTZ NOT NULL,
    totals JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (dataset_id, movement_code, interval_start)
);

COMMENT ON TABLE aforo_movement_counts IS 'Conteos agregados (15 min) por movimiento RILSA y clase vehicular';

CREATE TABLE IF NOT EXISTS aforo_dataset_history (
    id BIGSERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES aforo_datasets(id) ON DELETE CASCADE,
    action VARCHAR(128) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE aforo_dataset_history IS 'Historial de acciones realizadas sobre el dataset';

-- ======================================
-- Mensaje de confirmación
-- ======================================
\echo 'Schema created successfully!'
