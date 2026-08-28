"""Import all models so Alembic receives the complete metadata graph."""

from app.db.models.hazard import Hazard
from app.db.models.incident import Incident
from app.db.models.location import Location
from app.db.models.refresh_token import RefreshToken
from app.db.models.risk_assessment import RiskAssessment
from app.db.models.shelter import Shelter
from app.db.models.user import User
from app.db.models.user_device import UserDevice
from app.db.models.weather_observation import WeatherObservation

__all__ = [
    "Hazard",
    "Incident",
    "Location",
    "RiskAssessment",
    "RefreshToken",
    "Shelter",
    "User",
    "UserDevice",
    "WeatherObservation",
]
