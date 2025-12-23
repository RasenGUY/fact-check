from typing import Any, Optional
from fastapi import status

from app.schemas.response import StandardResponse, ErrorResponse, ErrorDetail


class ResponseTransformer:
    """
    Utility class for transforming API responses into a standardized format.
    """

    @staticmethod
    def success(
        data: Any = None,
        message: Optional[str] = "success",
        status_code: int = status.HTTP_200_OK,
    ) -> StandardResponse:
        """
        Transform a success response to the standard format.

        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code

        Returns:
            Standardized success response
        """
        return StandardResponse(
            success=True,
            data=data,
            message=message,
            status_code=status_code,
        )

    @staticmethod
    def error(
        message: str,
        error_code: str = "error",
        field: Optional[str] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: list[ErrorDetail] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> ErrorResponse:
        """
        Transform an error into the standard format.

        Args:
            message: Error message
            error_code: Error code
            field: Field that caused the error
            status_code: HTTP status code
            errors: List of additional errors
            data: Optional data to include in the response

        Returns:
            Standardized error response
        """
        error_detail = ErrorDetail(
            field=field,
            code=error_code,
            message=message,
        )

        return ErrorResponse(
            success=False,
            error=error_detail,
            errors=errors,
            status_code=status_code,
            data=data,
        )

    @staticmethod
    def validation_error(
        errors: list[dict[str, Any]],
        message: str = "Validation error",
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
    ) -> ErrorResponse:
        """
        Transform validation errors to the standard format.

        Args:
            errors: List of validation errors
            message: Error message
            status_code: HTTP status code

        Returns:
            Standardized error response
        """
        error_details = []

        for error in errors:
            loc = error.get("loc", [])
            field = loc[-1] if loc else None

            # For body validation errors, use the last part of the location
            if len(loc) > 1 and loc[0] == "body":
                field = ".".join(str(l) for l in loc[1:])

            error_details.append(
                ErrorDetail(
                    field=str(field) if field is not None else None,
                    code=None,
                    message=error.get("msg", "Validation error"),
                )
            )

        # Use the first error as the main error
        main_error = ErrorDetail(
            code=None,
            field=None,
            message=message,
        )

        return ErrorResponse(
            success=False,
            error=main_error,
            errors=error_details,
            status_code=status_code,
        )
