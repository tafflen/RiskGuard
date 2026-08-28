"""Controlled database enum types for the RiskGuard domain."""

from enum import StrEnum


class UserRole(StrEnum):
    CITIZEN = "citizen"
    RESPONDER = "responder"
    ADMINISTRATOR = "administrator"


class HazardType(StrEnum):
    FLOOD = "flood"
    CYCLONE = "cyclone"
    LANDSLIDE = "landslide"
    WILDFIRE = "wildfire"
    EARTHQUAKE = "earthquake"
    STORM = "storm"
    EXTREME_RAINFALL = "extreme_rainfall"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ShelterStatus(StrEnum):
    AVAILABLE = "available"
    LIMITED = "limited"
    FULL = "full"
    CLOSED = "closed"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
