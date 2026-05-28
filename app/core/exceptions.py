import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "internal_error"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None):
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


class RepositoryNotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "repository_not_found"

    def __init__(self, repository_id: int):
        super().__init__(f"Repository record {repository_id} was not found.")


class DuplicateRepository(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "duplicate_repository"

    def __init__(self, external_id: str):
        super().__init__(f"Repository '{external_id}' already exists.")


class ExternalRepositoryNotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "external_repository_not_found"

    def __init__(self, external_id: str):
        super().__init__(f"GitHub repository '{external_id}' was not found.")


class ExternalServiceUnavailable(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "external_service_unavailable"

    def __init__(self, external_id: str):
        super().__init__(f"GitHub could not be reached while fetching '{external_id}'.")


class ExternalServiceError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "external_service_error"

    def __init__(self, external_id: str, upstream_status: int | None = None):
        details = {"upstream_status": upstream_status} if upstream_status else {}
        super().__init__(
            f"GitHub returned an upstream error while fetching '{external_id}'.",
            details=details,
        )


def _payload(error: AppError) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": {
            "code": error.code,
            "message": error.message,
        }
    }
    if error.details:
        body["error"]["details"] = error.details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.info(
            "Handled application error",
            extra={"path": request.url.path, "code": exc.code, "status": exc.status_code},
        )
        return JSONResponse(status_code=exc.status_code, content=_payload(exc))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", extra={"path": request.url.path})
        fallback = AppError()
        return JSONResponse(status_code=fallback.status_code, content=_payload(fallback))
