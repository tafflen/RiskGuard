"""Small, transparent deterministic rules used when no validated ML model is loaded."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuleResult:
    score: float
    factors: list[str]


def evaluate(inside_hazard: bool, severity: float, incident_count: int) -> RuleResult:
    score = 0.0
    factors: list[str] = []
    if inside_hazard:
        score += 55
        factors.append("Location is inside an active hazard region.")
    if severity > 0:
        score += min(25, severity * 25)
        factors.append("Active hazard severity increases risk.")
    if incident_count:
        score += min(10, incident_count * 3)
        factors.append("Nearby unresolved incidents increase risk.")
    return RuleResult(min(100, score), factors)
