import json
from fastapi import HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Any, Union

from app.api.transformers import ResponseTransformer
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ResponseTransformerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to transform all API responses to a standardized format.
    Skips transformation for specified excluded paths.
    """

    def __init__(self, app, exclude_paths=None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/", "/docs", "/redoc", "/openapi.json", "/health"]

    async def dispatch(self, request: Request, call_next):
        if self._should_skip_path(request):
            return await call_next(request)

        try:
            # Get the original response from downstream handlers.
            original_response = await call_next(request)

            # Only process JSON responses.
            if not self._is_json_response(original_response):
                return original_response

            # Read and parse the response body.
            body, success = await self._read_response_body(original_response)
            if not success:
                return body

            body_json, success = self._parse_json_body(body, original_response)
            if not success:
                return body_json

            if original_response.status_code < 400:
                transformed = ResponseTransformer.success(
                    data=body_json, status_code=original_response.status_code
                )
            else:
                # For error responses, check if it's a validation error.
                error_message = self._extract_error_message(body_json)
                if "validation error" in str(error_message).lower():
                    # Use a specific transformer for validation errors.
                    transformed = ResponseTransformer.validation_error(
                        errors=body_json.get("detail", error_message), status_code=422
                    )
                else:
                    # Use a generic error transformer.
                    transformed = ResponseTransformer.error(
                        message=str(error_message),
                        error_code=f"http_{original_response.status_code}",
                        status_code=original_response.status_code,
                    )

            return self._create_json_response(
                transformed.model_dump(exclude_none=True),
                transformed.status_code,
                original_response.headers,
            )

        except RequestValidationError as exc:
            logger.error("Request validation error", error=str(exc))
            return self._handle_validation_error(exc)
        except ValidationError as exc:
            logger.error("Pydantic validation error", error=str(exc))
            return self._handle_pydantic_validation_error(exc)
        except HTTPException as exc:
            logger.error("HTTP exception", error=str(exc))
            return self._handle_http_exception(exc)
        except Exception as exc:
            logger.error("General exception", error=str(exc))
            return self._handle_general_exception(exc)

    def _should_skip_path(self, request: Request) -> bool:
        return any(request.url.path.endswith(path) for path in self.exclude_paths)

    def _is_json_response(self, response) -> bool:
        return "application/json" in response.headers.get("content-type", "")

    async def _read_response_body(
        self, response
    ) -> tuple[Union[bytes, Response], bool]:
        try:
            if hasattr(response, "body_iterator"):
                chunks = []
                async for chunk in response.body_iterator:
                    chunks.append(chunk)
                return b"".join(chunks), True
            elif hasattr(response, "body"):
                return response.body, True
            else:
                return response, False
        except Exception:
            return response, False

    def _parse_json_body(
        self, body: bytes, original_response
    ) -> tuple[Union[dict[str, Any], Response], bool]:
        try:
            return json.loads(body.decode("utf-8")), True
        except Exception:
            # If parsing fails, return the original body unchanged.
            return (
                Response(
                    content=body,
                    status_code=original_response.status_code,
                    headers=dict(original_response.headers),
                    media_type=original_response.headers.get("content-type", ""),
                ),
                False,
            )

    def _extract_error_message(self, body_json: dict[str, Any]) -> str:
        if isinstance(body_json, dict) and "detail" in body_json:
            return body_json["detail"]
        return "An error occurred"

    def _create_json_response(
        self, content: dict[str, Any], status_code: int, headers: dict[str, str]
    ) -> JSONResponse:
        clean_headers = {
            k: v
            for k, v in headers.items()
            if k.lower() not in ("content-length", "content-encoding")
        }
        return JSONResponse(content=content, status_code=status_code, headers=clean_headers)

    def _handle_validation_error(self, exc: RequestValidationError) -> JSONResponse:
        errors = json.loads(exc.json())
        transformed = ResponseTransformer.validation_error(errors=errors)
        return JSONResponse(
            content=transformed.model_dump(exclude_none=True),
            status_code=transformed.status_code,
        )

    def _handle_pydantic_validation_error(self, exc: ValidationError) -> JSONResponse:
        errors = exc.errors()
        transformed = ResponseTransformer.validation_error(errors=errors)
        return JSONResponse(
            content=transformed.model_dump(exclude_none=True),
            status_code=transformed.status_code,
        )

    def _handle_http_exception(self, exc: HTTPException) -> JSONResponse:
        transformed = ResponseTransformer.error(
            message=str(exc.detail),
            status_code=exc.status_code,
            error_code=f"http_{exc.status_code}",
        )
        return JSONResponse(
            content=transformed.model_dump(exclude_none=True), status_code=exc.status_code
        )

    def _handle_general_exception(self, exc: Exception) -> JSONResponse:
        transformed = ResponseTransformer.error(
            message=str(exc),
            error_code="internal_server_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        return JSONResponse(
            content=transformed.model_dump(exclude_none=True),
            status_code=transformed.status_code,
        )
