"""Tests for credential redaction before messages reach log handlers."""

import logging

from app.core.logging import SensitiveDataFilter


def test_sensitive_logging_filter_redacts_credentials() -> None:
    record = logging.LogRecord(
        "riskguard", logging.INFO, __file__, 1, "password=secret token=jwt-value", (), None
    )

    assert SensitiveDataFilter().filter(record)
    assert "secret" not in record.msg
    assert "jwt-value" not in record.msg
    assert "[REDACTED]" in record.msg
