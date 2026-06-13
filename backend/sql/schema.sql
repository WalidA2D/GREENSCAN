-- ============================================================================
-- GreenScan - Schéma PostgreSQL
-- Appliqué automatiquement par docker-compose au 1er démarrage du volume.
-- (En dehors de Docker, les tables sont aussi créées par SQLAlchemy init_db().)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    full_name   VARCHAR(120) NOT NULL,
    email       VARCHAR(160) UNIQUE NOT NULL,
    profile     VARCHAR(40)  NOT NULL DEFAULT 'standard',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS homes (
    id                   SERIAL PRIMARY KEY,
    owner_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                 VARCHAR(120) NOT NULL,
    home_type            VARCHAR(40)  NOT NULL,
    surface_m2           DOUBLE PRECISION NOT NULL,
    construction_year    INTEGER,
    dpe                  VARCHAR(2)   NOT NULL DEFAULT 'D',
    orientation          VARCHAR(20),
    occupants_count      INTEGER      NOT NULL DEFAULT 2,
    heating_type         VARCHAR(30)  NOT NULL DEFAULT 'électrique',
    contracted_power_kva DOUBLE PRECISION NOT NULL DEFAULT 9.0,
    has_solar_panels     BOOLEAN      NOT NULL DEFAULT FALSE,
    has_ev               BOOLEAN      NOT NULL DEFAULT FALSE,
    city                 VARCHAR(80)  NOT NULL DEFAULT 'Paris',
    monthly_budget_eur   DOUBLE PRECISION NOT NULL DEFAULT 120.0
);
CREATE INDEX IF NOT EXISTS ix_homes_owner ON homes(owner_id);

CREATE TABLE IF NOT EXISTS rooms (
    id                 SERIAL PRIMARY KEY,
    home_id            INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    name               VARCHAR(80) NOT NULL,
    room_type          VARCHAR(40) NOT NULL,
    surface_m2         DOUBLE PRECISION NOT NULL DEFAULT 12.0,
    floor              INTEGER NOT NULL DEFAULT 0,
    usual_occupants    INTEGER NOT NULL DEFAULT 1,
    target_temperature DOUBLE PRECISION NOT NULL DEFAULT 20.0
);
CREATE INDEX IF NOT EXISTS ix_rooms_home ON rooms(home_id);

CREATE TABLE IF NOT EXISTS equipments (
    id                SERIAL PRIMARY KEY,
    home_id           INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    room_id           INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    name              VARCHAR(80) NOT NULL,
    equipment_type    VARCHAR(40) NOT NULL,
    rated_power_w     DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    daily_usage_hours DOUBLE PRECISION NOT NULL DEFAULT 2.0,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    criticality       INTEGER NOT NULL DEFAULT 2
);
CREATE INDEX IF NOT EXISTS ix_equipments_home ON equipments(home_id);
CREATE INDEX IF NOT EXISTS ix_equipments_room ON equipments(room_id);

CREATE TABLE IF NOT EXISTS consumption_records (
    id                      BIGSERIAL PRIMARY KEY,
    home_id                 INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    room_id                 INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    equipment_id            INTEGER REFERENCES equipments(id) ON DELETE CASCADE,
    timestamp               TIMESTAMPTZ NOT NULL,
    energy_consumption_kwh  DOUBLE PRECISION NOT NULL,
    energy_cost_eur         DOUBLE PRECISION NOT NULL DEFAULT 0,
    tariff_type             VARCHAR(2) NOT NULL DEFAULT 'HP',
    heating_consumption_kwh DOUBLE PRECISION NOT NULL DEFAULT 0,
    solar_production_kwh    DOUBLE PRECISION NOT NULL DEFAULT 0,
    ev_charging_kwh         DOUBLE PRECISION NOT NULL DEFAULT 0,
    occupants_present       INTEGER NOT NULL DEFAULT 0,
    home_presence           BOOLEAN NOT NULL DEFAULT TRUE,
    co2_kg                  DOUBLE PRECISION NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_consumption_home_ts ON consumption_records(home_id, timestamp);

CREATE TABLE IF NOT EXISTS weather_records (
    id                  BIGSERIAL PRIMARY KEY,
    home_id             INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    timestamp           TIMESTAMPTZ NOT NULL,
    outdoor_temperature DOUBLE PRECISION NOT NULL,
    humidity            DOUBLE PRECISION NOT NULL DEFAULT 60,
    wind_speed          DOUBLE PRECISION NOT NULL DEFAULT 10,
    solar_radiation     DOUBLE PRECISION NOT NULL DEFAULT 0,
    cloud_cover         DOUBLE PRECISION NOT NULL DEFAULT 50,
    weather_condition   VARCHAR(20) NOT NULL DEFAULT 'nuageux'
);
CREATE INDEX IF NOT EXISTS ix_weather_home_ts ON weather_records(home_id, timestamp);

CREATE TABLE IF NOT EXISTS predictions (
    id          SERIAL PRIMARY KEY,
    home_id     INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    kind        VARCHAR(40) NOT NULL,
    target_date TIMESTAMPTZ NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    unit        VARCHAR(10) NOT NULL DEFAULT 'kWh',
    model_name  VARCHAR(40) NOT NULL DEFAULT 'RandomForest',
    metrics     JSONB,
    detail      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_predictions_home_kind ON predictions(home_id, kind);

CREATE TABLE IF NOT EXISTS alerts (
    id             SERIAL PRIMARY KEY,
    home_id        INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    room_id        INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    equipment_id   INTEGER REFERENCES equipments(id) ON DELETE SET NULL,
    category       VARCHAR(40) NOT NULL,
    title          VARCHAR(160) NOT NULL,
    description    TEXT NOT NULL,
    level          VARCHAR(10) NOT NULL DEFAULT 'info',
    recommendation TEXT NOT NULL DEFAULT '',
    detected_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_resolved    BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_alerts_home ON alerts(home_id);

CREATE TABLE IF NOT EXISTS recommendations (
    id                   SERIAL PRIMARY KEY,
    home_id              INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    room_id              INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    code                 VARCHAR(40) NOT NULL,
    action               TEXT NOT NULL,
    gain_eur_month       DOUBLE PRECISION NOT NULL DEFAULT 0,
    gain_kwh_month       DOUBLE PRECISION NOT NULL DEFAULT 0,
    co2_avoided_kg_month DOUBLE PRECISION NOT NULL DEFAULT 0,
    impact               VARCHAR(10) NOT NULL DEFAULT 'moyen',
    difficulty           VARCHAR(10) NOT NULL DEFAULT 'facile',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_recommendations_home ON recommendations(home_id);

CREATE TABLE IF NOT EXISTS kpi_results (
    id          SERIAL PRIMARY KEY,
    home_id     INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    code        VARCHAR(40) NOT NULL,
    label       VARCHAR(80) NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    unit        VARCHAR(16) NOT NULL DEFAULT '',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_kpi_home_code ON kpi_results(home_id, code);

CREATE TABLE IF NOT EXISTS simulations (
    id                   SERIAL PRIMARY KEY,
    home_id              INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
    scenario             VARCHAR(40) NOT NULL,
    params               JSONB,
    baseline_kwh_month   DOUBLE PRECISION NOT NULL DEFAULT 0,
    simulated_kwh_month  DOUBLE PRECISION NOT NULL DEFAULT 0,
    saving_eur_month     DOUBLE PRECISION NOT NULL DEFAULT 0,
    saving_kwh_month     DOUBLE PRECISION NOT NULL DEFAULT 0,
    co2_avoided_kg_month DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_simulations_home ON simulations(home_id);
