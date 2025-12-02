from fastapi.responses import JSONResponse
from typing import Any, Optional, Dict
from http import HTTPStatus
import structlog
from app.models.schemas import SuccessResponse, ErrorResponse

logger = structlog.get_logger()


class APIResponseHelper:
    """Helper class for consistent API responses (аналог ApiResponseHelper)."""
    
    @staticmethod
    def success_response(
        data: Any = None,
        message: Optional[str] = None,
        status_code: int = HTTPStatus.OK,
        name: str = "data"
    ) -> JSONResponse:
        """
        Create success response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            name: Data field name
        """
        response_data = {
            "success": True,
            name: data
        }
        
        if message:
            response_data["message"] = message
        
        logger.info("Success response", status_code=status_code, message=message)
        return JSONResponse(content=response_data, status_code=status_code)
    
    @staticmethod
    def error_response(
        message: str,
        status_code: int = HTTPStatus.BAD_REQUEST,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        Create error response.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Error code
            details: Additional error details
        """
        # Sanitize error message (аналог sanitizeErrorMessage)
        safe_message = APIResponseHelper._sanitize_error_message(message)
        
        response_data = {
            "success": False,
            "message": safe_message
        }
        
        if error_code:
            response_data["error_code"] = error_code
        
        if details:
            response_data["details"] = details
        
        logger.warning("Error response", status_code=status_code, message=safe_message, error_code=error_code)
        return JSONResponse(content=response_data, status_code=status_code)
    
    @staticmethod
    def validation_error_response(
        errors: Dict[str, Any],
        message: str = "Validation failed"
    ) -> JSONResponse:
        """Create validation error response."""
        return APIResponseHelper.error_response(
            message=message,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details={"validation_errors": errors}
        )
    
    @staticmethod
    def not_found_response(
        resource: str = "Resource",
        message: Optional[str] = None
    ) -> JSONResponse:
        """Create not found response."""
        if not message:
            message = f"{resource} not found"
        
        return APIResponseHelper.error_response(
            message=message,
            status_code=HTTPStatus.NOT_FOUND,
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def unauthorized_response(
        message: str = "Unauthorized"
    ) -> JSONResponse:
        """Create unauthorized response."""
        return APIResponseHelper.error_response(
            message=message,
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )
    
    @staticmethod
    def forbidden_response(
        message: str = "Forbidden"
    ) -> JSONResponse:
        """Create forbidden response."""
        return APIResponseHelper.error_response(
            message=message,
            status_code=HTTPStatus.FORBIDDEN,
            error_code="FORBIDDEN"
        )
    
    @staticmethod
    def internal_error_response(
        message: str = "Internal server error"
    ) -> JSONResponse:
        """Create internal server error response."""
        return APIResponseHelper.error_response(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR"
        )
    
    @staticmethod
    def _sanitize_error_message(message: str) -> str:
        """
        Sanitize error message to remove potentially sensitive information.
        Аналог sanitizeErrorMessage из Laravel.
        """
        import re
        
        # Remove file paths
        message = re.sub(r'/[^\s]+\.py', '[file]', message)
        
        # Remove line numbers
        message = re.sub(r'line \d+', 'line [hidden]', message)
        
        # Remove stack traces
        message = re.sub(r'Stack trace:.*$', '[stack trace hidden]', message, flags=re.DOTALL)
        
        # Remove database connection info
        message = re.sub(r'SQLSTATE\[.*?\]', '[database error]', message)
        
        # Remove class paths
        message = re.sub(r'App\\[^\\s]+', '[class]', message)
        
        return message


# Convenience functions for direct use
def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = HTTPStatus.OK,
    name: str = "data"
) -> JSONResponse:
    """Convenience function for success response."""
    return APIResponseHelper.success_response(data, message, status_code, name)


def error_response(
    message: str,
    status_code: int = HTTPStatus.BAD_REQUEST,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Convenience function for error response."""
    return APIResponseHelper.error_response(message, status_code, error_code, details)


def validation_error_response(
    errors: Dict[str, Any],
    message: str = "Validation failed"
) -> JSONResponse:
    """Convenience function for validation error response."""
    return APIResponseHelper.validation_error_response(errors, message)


def not_found_response(
    resource: str = "Resource",
    message: Optional[str] = None
) -> JSONResponse:
    """Convenience function for not found response."""
    return APIResponseHelper.not_found_response(resource, message)


def unauthorized_response(message: str = "Unauthorized") -> JSONResponse:
    """Convenience function for unauthorized response."""
    return APIResponseHelper.unauthorized_response(message)


def forbidden_response(message: str = "Forbidden") -> JSONResponse:
    """Convenience function for forbidden response."""
    return APIResponseHelper.forbidden_response(message)


def internal_error_response(message: str = "Internal server error") -> JSONResponse:
    """Convenience function for internal error response."""
    return APIResponseHelper.internal_error_response(message)
