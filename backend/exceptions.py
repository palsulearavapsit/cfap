class AppException(Exception):
    """Base application exception for structured API responses."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(AppException):
    """Raised when incoming questionnaire input fails validation constraints."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class AuthenticationError(AppException):
    """Raised when authentication credentials or timelapsed signatures are invalid."""

    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class ResourceNotFound(AppException):
    """Raised when a requested resource is not found in the database."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)
