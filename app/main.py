"""Application composition root for the RiskGuard API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    alerts,
    auth,
    disaster,
    devices,
    hazards,
    incidents,
    locations,
    risk,
    routes,
    shelters,
    demo,
    users,
    weather,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import install_exception_handlers
from app.core.logging import configure_logging


def create_application(settings: Settings | None = None) -> FastAPI:
    """Create a configured FastAPI application without connecting to dependencies."""
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    application = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
        debug=active_settings.debug,
        docs_url="/docs" if active_settings.is_development else None,
        redoc_url="/redoc" if active_settings.is_development else None,
        openapi_url="/openapi.json" if active_settings.is_development else None,
    )
    application.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    install_exception_handlers(application)
    application.include_router(auth.router, prefix=active_settings.api_v1_prefix)
    application.include_router(users.router, prefix=active_settings.api_v1_prefix)
    application.include_router(locations.router, prefix=active_settings.api_v1_prefix)
    application.include_router(hazards.router, prefix=active_settings.api_v1_prefix)
    application.include_router(shelters.router, prefix=active_settings.api_v1_prefix)
    application.include_router(incidents.router, prefix=active_settings.api_v1_prefix)
    application.include_router(devices.router, prefix=active_settings.api_v1_prefix)
    application.include_router(risk.router, prefix=active_settings.api_v1_prefix)
    application.include_router(routes.router, prefix=active_settings.api_v1_prefix)
    application.include_router(weather.router, prefix=active_settings.api_v1_prefix)
    application.include_router(alerts.router, prefix=active_settings.api_v1_prefix)
    application.include_router(
    disaster.router,
    prefix=active_settings.api_v1_prefix,
)
    application.include_router(
    demo.router,
    prefix=active_settings.api_v1_prefix,
)
    @application.get("/health", tags=["Health"], summary="Application liveness check")
    async def health() -> dict[str, str]:
        """Return process liveness without probing external dependencies."""
        return {"status": "ok"}

    return application


app = create_application()
