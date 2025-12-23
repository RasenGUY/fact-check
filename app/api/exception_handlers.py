from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.schemas.response import ErrorResponse
from app.api.transformers import ResponseTransformer
from app.utils.logging import get_logger

logger = get_logger(__name__)


def add_exception_handlers(app: FastAPI):
    """
    Add exception handlers to the FastAPI app.

    Args:
        app: FastAPI application
    """

    def log_error(response: ErrorResponse):
        logger.error("Request error", error=response)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle request validation errors."""
        errors = exc.errors()
        transformed = ResponseTransformer.validation_error(errors)
        log_error(transformed)
        return JSONResponse(
            content=transformed.model_dump(exclude_none=True),
            status_code=transformed.status_code,
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        """Handle Pydantic validation errors."""
        errors = exc.errors()
        transformed = ResponseTransformer.validation_error(errors)
        log_error(transformed)
        return JSONResponse(
            content=transformed.model_dump(exclude_none=True),
            status_code=transformed.status_code,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        transformed = ResponseTransformer.error(
            message=str(exc),
            error_code="internal_server_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        log_error(transformed)
        return JSONResponse(
            content=transformed.model_dump(exclude_none=True),
            status_code=transformed.status_code,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        transformed = ResponseTransformer.error(
            message=exc.detail,
            error_code=str(exc.status_code),
            status_code=exc.status_code,
        )
        log_error(transformed)
        return JSONResponse(
            content=transformed.model_dump(exclude_none=True, mode="json"),
            status_code=transformed.status_code,
        )
