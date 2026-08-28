"""Risk level mapping and conservative confidence fusion."""

from app.db.types import RiskLevel


def final_score(rule_score: float, confidence: float) -> float:
    return round(max(0, min(100, rule_score * max(0, min(1, confidence)))), 2)


def level(score: float) -> RiskLevel:
    if score >= 80:
        return RiskLevel.CRITICAL
    if score >= 55:
        return RiskLevel.HIGH
    if score >= 25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
