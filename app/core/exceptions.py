"""Safe, consistent error handling for public API responses."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class RiskGuardError(Exception):
    """Base controlled error that is safe to serialize for API clients."""

    def __init__(
        self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def error_response(request: Request, code: str, message: str, status_code: int) -> JSONResponse:
    """Construct the standard error envelope without internal error details."""
    request_id = getattr(request.state, "request_id", "unknown")
    body: dict[str, Any] = {
        "success": False,
        "error": {"code": code, "message": message},
        "request_id": request_id,
    }
    return JSONResponse(status_code=status_code, content=body)


def install_exception_handlers(application: FastAPI) -> None:
    """Register controlled-error serialization; framework errors are added with the API layer."""

    @application.exception_handler(RiskGuardError)
    async def handle_riskguard_error(request: Request, exc: RiskGuardError) -> JSONResponse:
        return error_response(request, exc.code, exc.message, exc.status_code)
