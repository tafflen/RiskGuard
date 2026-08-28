"""Structured, sensitive-data-conscious application logging."""

import logging
import re
import sys

_SENSITIVE_VALUE = re.compile(
    r"(?i)\b(password|token|authorization|secret)\b\s*([=:])\s*([^\s,;]+)"
)


class SensitiveDataFilter(logging.Filter):
    """Redact common credential fields before they reach a configured log handler."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        record.msg = _SENSITIVE_VALUE.sub(r"\1\2[REDACTED]", message)
        record.args = ()
        return True


def configure_logging(level: str) -> None:
    """Configure process logging once; endpoint middleware is added with the API phase."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(SensitiveDataFilter())
