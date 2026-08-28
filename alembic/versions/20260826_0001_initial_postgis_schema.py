# ruff: noqa: E501
"""Initial PostGIS schema for RiskGuard.

Revision ID: 20260826_0001
Revises:
Create Date: 2026-08-26
"""

from alembic import op

revision = "20260826_0001"
down_revision = None
branch_labels = None
depends_on = None


def _execute_statements(sql: str) -> None:
    """Execute one PostgreSQL statement at a time for asyncpg compatibility.

    asyncpg prepares statements and rejects semicolon-separated SQL batches. The parser preserves
    PostgreSQL dollar-quoted trigger functions, whose bodies legitimately contain semicolons.
    """
    statement: list[str] = []
    in_dollar_quote = False
    position = 0
    while position < len(sql):
        if sql[position : position + 2] == "$$":
            in_dollar_quote = not in_dollar_quote
            statement.append("$$")
            position += 2
            continue
        character = sql[position]
        if character == ";" and not in_dollar_quote:
            command = "".join(statement).strip()
            if command:
                op.execute(command)
            statement = []
        else:
            statement.append(character)
        position += 1
    command = "".join(statement).strip()
    if command:
        op.execute(command)


def upgrade() -> None:
    """Create extension, relational schema, integrity triggers, and spatial indexes."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    _execute_statements(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY, email VARCHAR(320) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(200) NOT NULL, role VARCHAR(13) NOT NULL DEFAULT 'citizen',
            is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_users_role CHECK (role IN ('citizen','responder','administrator'))
        );
        CREATE TABLE user_devices (
            id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            device_id VARCHAR(255) NOT NULL, fcm_token VARCHAR(4096), platform VARCHAR(32) NOT NULL,
            last_seen TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_user_devices_user_device_identity UNIQUE (user_id, device_id)
        );
        CREATE TABLE locations (
            id UUID PRIMARY KEY, user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
            accuracy DOUBLE PRECISION, geom geometry(POINT,4326) NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_locations_latitude_range CHECK (latitude >= -90 AND latitude <= 90),
            CONSTRAINT ck_locations_longitude_range CHECK (longitude >= -180 AND longitude <= 180),
            CONSTRAINT ck_locations_accuracy_nonnegative CHECK (accuracy IS NULL OR accuracy >= 0)
        );
        CREATE TABLE hazards (
            id UUID PRIMARY KEY, hazard_type VARCHAR(100) NOT NULL, severity VARCHAR(8) NOT NULL,
            confidence NUMERIC(4,3) NOT NULL, source VARCHAR(200) NOT NULL,
            valid_from TIMESTAMPTZ NOT NULL, valid_until TIMESTAMPTZ,
            geometry geometry(MULTIPOLYGON,4326) NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_hazards_severity CHECK (severity IN ('low','medium','high','critical')),
            CONSTRAINT ck_hazards_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
            CONSTRAINT ck_hazards_validity_range CHECK (valid_until IS NULL OR valid_until >= valid_from)
        );
        CREATE TABLE shelters (
            id UUID PRIMARY KEY, name VARCHAR(300) NOT NULL, capacity INTEGER NOT NULL,
            current_occupancy INTEGER NOT NULL DEFAULT 0, status VARCHAR(9) NOT NULL,
            latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
            geom geometry(POINT,4326) NOT NULL, facilities JSONB NOT NULL DEFAULT '{}'::jsonb,
            contact_information JSONB NOT NULL DEFAULT '{}'::jsonb, verified_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_shelters_latitude_range CHECK (latitude >= -90 AND latitude <= 90),
            CONSTRAINT ck_shelters_longitude_range CHECK (longitude >= -180 AND longitude <= 180),
            CONSTRAINT ck_shelters_capacity_nonnegative CHECK (capacity >= 0),
            CONSTRAINT ck_shelters_occupancy_nonnegative CHECK (current_occupancy >= 0),
            CONSTRAINT ck_shelters_occupancy_within_capacity CHECK (current_occupancy <= capacity),
            CONSTRAINT ck_shelters_status CHECK (status IN ('available','limited','full','closed'))
        );
        CREATE TABLE incidents (
            id UUID PRIMARY KEY, incident_type VARCHAR(100) NOT NULL, severity VARCHAR(8) NOT NULL,
            description TEXT, latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
            geom geometry(POINT,4326) NOT NULL, source VARCHAR(200) NOT NULL, reported_at TIMESTAMPTZ NOT NULL,
            resolved_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_incidents_latitude_range CHECK (latitude >= -90 AND latitude <= 90),
            CONSTRAINT ck_incidents_longitude_range CHECK (longitude >= -180 AND longitude <= 180),
            CONSTRAINT ck_incidents_severity CHECK (severity IN ('low','medium','high','critical')),
            CONSTRAINT ck_incidents_resolution_range CHECK (resolved_at IS NULL OR resolved_at >= reported_at)
        );
        CREATE TABLE weather_observations (
            id UUID PRIMARY KEY, source VARCHAR(200) NOT NULL, latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL, geom geometry(POINT,4326) NOT NULL,
            rainfall_mm NUMERIC(10,3), temperature NUMERIC(6,3), wind_speed NUMERIC(8,3),
            humidity NUMERIC(5,2), pressure NUMERIC(8,2), observed_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_weather_observations_latitude_range CHECK (latitude >= -90 AND latitude <= 90),
            CONSTRAINT ck_weather_observations_longitude_range CHECK (longitude >= -180 AND longitude <= 180),
            CONSTRAINT ck_weather_observations_rainfall_nonnegative CHECK (rainfall_mm IS NULL OR rainfall_mm >= 0),
            CONSTRAINT ck_weather_observations_humidity_range CHECK (humidity IS NULL OR humidity >= 0 AND humidity <= 100)
        );
        CREATE TABLE risk_assessments (
            id UUID PRIMARY KEY, user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
            geom geometry(POINT,4326) NOT NULL, risk_score NUMERIC(5,2) NOT NULL,
            risk_level VARCHAR(8) NOT NULL, model_version VARCHAR(100) NOT NULL, confidence NUMERIC(4,3) NOT NULL,
            factors JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_risk_assessments_latitude_range CHECK (latitude >= -90 AND latitude <= 90),
            CONSTRAINT ck_risk_assessments_longitude_range CHECK (longitude >= -180 AND longitude <= 180),
            CONSTRAINT ck_risk_assessments_score_range CHECK (risk_score >= 0 AND risk_score <= 100),
            CONSTRAINT ck_risk_assessments_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
            CONSTRAINT ck_risk_assessments_risk_level CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL'))
        );
        """
    )
    _execute_statements(
        """
        CREATE FUNCTION riskguard_validate_point_geometry() RETURNS trigger AS $$
        BEGIN
            IF ST_SRID(NEW.geom) <> 4326 OR GeometryType(NEW.geom) <> 'POINT'
               OR abs(ST_Y(NEW.geom) - NEW.latitude) > 0.0000001
               OR abs(ST_X(NEW.geom) - NEW.longitude) > 0.0000001 THEN
                RAISE EXCEPTION 'geom must be an SRID 4326 POINT matching latitude and longitude';
            END IF;
            RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        CREATE FUNCTION riskguard_validate_hazard_geometry() RETURNS trigger AS $$
        BEGIN
            IF ST_SRID(NEW.geometry) <> 4326 OR GeometryType(NEW.geometry) <> 'MULTIPOLYGON' THEN
                RAISE EXCEPTION 'hazard geometry must be an SRID 4326 MULTIPOLYGON';
            END IF;
            RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_locations_validate_geom BEFORE INSERT OR UPDATE ON locations FOR EACH ROW EXECUTE FUNCTION riskguard_validate_point_geometry();
        CREATE TRIGGER trg_shelters_validate_geom BEFORE INSERT OR UPDATE ON shelters FOR EACH ROW EXECUTE FUNCTION riskguard_validate_point_geometry();
        CREATE TRIGGER trg_incidents_validate_geom BEFORE INSERT OR UPDATE ON incidents FOR EACH ROW EXECUTE FUNCTION riskguard_validate_point_geometry();
        CREATE TRIGGER trg_weather_validate_geom BEFORE INSERT OR UPDATE ON weather_observations FOR EACH ROW EXECUTE FUNCTION riskguard_validate_point_geometry();
        CREATE TRIGGER trg_risk_assessments_validate_geom BEFORE INSERT OR UPDATE ON risk_assessments FOR EACH ROW EXECUTE FUNCTION riskguard_validate_point_geometry();
        CREATE TRIGGER trg_hazards_validate_geom BEFORE INSERT OR UPDATE ON hazards FOR EACH ROW EXECUTE FUNCTION riskguard_validate_hazard_geometry();
        CREATE INDEX ix_users_email ON users (email);
        CREATE INDEX ix_user_devices_user_id ON user_devices (user_id);
        CREATE INDEX ix_user_devices_device_id ON user_devices (device_id);
        CREATE INDEX ix_locations_user_id ON locations (user_id);
        CREATE INDEX ix_locations_timestamp ON locations (timestamp);
        CREATE INDEX ix_locations_geom_gist ON locations USING GIST (geom);
        CREATE INDEX ix_hazards_hazard_type ON hazards (hazard_type);
        CREATE INDEX ix_hazards_severity ON hazards (severity);
        CREATE INDEX ix_hazards_valid_from ON hazards (valid_from);
        CREATE INDEX ix_hazards_valid_until ON hazards (valid_until);
        CREATE INDEX ix_hazards_source ON hazards (source);
        CREATE INDEX ix_hazards_geometry_gist ON hazards USING GIST (geometry);
        CREATE INDEX ix_shelters_status ON shelters (status);
        CREATE INDEX ix_shelters_geom_gist ON shelters USING GIST (geom);
        CREATE INDEX ix_incidents_incident_type ON incidents (incident_type);
        CREATE INDEX ix_incidents_severity ON incidents (severity);
        CREATE INDEX ix_incidents_reported_at ON incidents (reported_at);
        CREATE INDEX ix_incidents_geom_gist ON incidents USING GIST (geom);
        CREATE INDEX ix_weather_observations_source ON weather_observations (source);
        CREATE INDEX ix_weather_observations_observed_at ON weather_observations (observed_at);
        CREATE INDEX ix_weather_observations_geom_gist ON weather_observations USING GIST (geom);
        CREATE INDEX ix_risk_assessments_user_id ON risk_assessments (user_id);
        CREATE INDEX ix_risk_assessments_created_at ON risk_assessments (created_at);
        CREATE INDEX ix_risk_assessments_geom_gist ON risk_assessments USING GIST (geom);
        """
    )


def downgrade() -> None:
    """Drop application schema while preserving a shared PostGIS extension."""
    op.execute(
        "DROP TABLE IF EXISTS risk_assessments, weather_observations, incidents, shelters, hazards, locations, user_devices, users CASCADE"
    )
    op.execute("DROP FUNCTION IF EXISTS riskguard_validate_hazard_geometry()")
    op.execute("DROP FUNCTION IF EXISTS riskguard_validate_point_geometry()")
