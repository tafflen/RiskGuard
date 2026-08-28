# RiskGuard Backend

RiskGuard is a security-conscious backend for disaster-risk intelligence. It is designed to calculate explainable location risk, identify safe shelters, evaluate route exposure, and deliver verified emergency notifications. The system must not present demo data, unvalidated models, or unavailable external information as live disaster intelligence.

## Status

**Phase 2 complete in code:** Phase 1 foundations plus typed SQLAlchemy/PostGIS models, Alembic migration, database repository primitives, demo seed data, and a Docker PostGIS definition are in place. Live PostgreSQL/PostGIS validation remains environment-dependent; see the Phase 2 section.

## Architecture

The application uses a modular monolith. FastAPI routes will depend on focused services, which use repositories for PostgreSQL/PostGIS access and adapters for Redis and external providers. This keeps disaster-critical decisions auditable while avoiding operational complexity that is not yet warranted.

```text
Flutter client -> FastAPI API -> services -> repositories -> PostgreSQL/PostGIS
                                  |              
                                  +-> provider adapters (weather, Mapbox, FCM, Redis)
                                  +-> risk engine (rules + optional ML)
```

## Local setup

1. Install Python 3.12 or newer and Docker Desktop for Windows.
2. In PowerShell, create and activate a virtual environment: `py -3.12 -m venv .venv`, then `.\.venv\Scripts\Activate.ps1`.
3. Install development dependencies: `pip install -e .[dev]`.
4. Copy `.env.example` to `.env`; set a local `POSTGRES_PASSWORD`, then update both database URLs to use it.
5. Start PostGIS: `docker compose up -d db`. Wait for `docker compose ps` to report `healthy`.
6. Apply the schema: `alembic upgrade head`.
7. Optionally insert simulated data only: `python -m scripts.seed_demo_data`.
8. Start the Phase 1 application: `uvicorn app.main:app --reload`.

The development server only exposes `GET /health`; it does not claim dependency readiness. Database, Redis, and `/ready` arrive in later phases.

## Quality checks

```text
ruff check .
mypy app
pytest
```

## Privacy and data lifecycle

Location handling will be data-minimized: precise location records are collected only for explicit user-facing safety functions, retained for a documented short period, access-controlled, and removable through a user data-deletion workflow. Retention enforcement and deletion endpoints will be implemented with the location model and service phases.

## Safety boundaries

- Demo or simulated data will be labelled as such at ingestion and response boundaries.
- Model metrics are never asserted without a validated dataset and evaluation run.
- External-provider outages must degrade confidence or use valid cached data, never silently create facts.
- A route is not described as safe merely because it is shortest.

## Planned implementation sequence

The project follows the phased plan in the engineering specification: data layer, identity, geospatial services, domain services, risk engine, ML/explainability, routing, Redis/FCM, complete APIs, tests, Docker, CI, and validation.

## Database and PostGIS (Phase 2)

The database uses PostgreSQL with PostGIS. Apply all schema changes through Alembic only:

```text
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe schema change"
```

Run local PostGIS in PowerShell with `$env:POSTGRES_PASSWORD='<local-secret>'; docker compose up -d db`. The isolated test database is started with `$env:POSTGRES_PASSWORD='<local-secret>'; docker compose --profile test up -d db-test`; set `TEST_DATABASE_URL` to that database before integration testing. Docker Desktop must be running. The Compose file intentionally creates only PostgreSQL/PostGIS in this phase; Redis is deferred to its designated phase.

All stored map columns use `geometry(..., 4326)` because this keeps spatial GiST indexing and topology operations direct and interoperable. Repository distance predicates explicitly cast operands to PostGIS `geography`, so `ST_DWithin` and `ST_Distance` use metres rather than longitude/latitude degrees. Hazards are active only if `valid_from <= now` and (`valid_until` is null or `valid_until >= now`).

Point rows are guarded by database triggers: SRID, point shape, latitude, longitude, and geometry must agree. User-device rows use `ON DELETE RESTRICT` to avoid accidental loss of notification-audit links. Locations and risk assessments use `ON DELETE SET NULL` to preserve safety-history integrity while detaching it from deleted users; a future deletion service will enforce retention and erasure policy deliberately.

### Retention recommendations

- Precise locations: retain only the shortest period necessary for the requested safety workflow (recommended 30 days or less), then aggregate or delete.
- Risk assessments: retain a documented, access-controlled operational window (recommended 90 days), then delete or irreversibly aggregate.
- Weather observations and incidents: retain according to verified source provenance and disaster-management records policy; do not treat DEMO data as operational data.
- Security/audit data: retain minimally, access-control it, and redact tokens and precise historic locations.

`python -m scripts.seed_demo_data` inserts only `DEMO_DATA_NOT_LIVE` records and refuses staging/production execution.

## Authentication (Phase 3)

The API exposes `POST /api/v1/auth/register`, `login`, `refresh`, and `logout`, plus
`GET`, `PATCH`, and `DELETE /api/v1/users/me`. Passwords are hashed with Argon2id; they are never
logged or returned. The password policy requires at least 12 characters, uppercase, lowercase,
numeric, and symbol characters.
Access JWTs are short-lived. Refresh JWTs are rotated and their opaque IDs are stored server-side so
logout and reuse prevention work. Apply the `20260827_0002` Alembic migration before enabling these
endpoints against any existing database.
