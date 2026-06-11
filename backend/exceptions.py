class ValidationError(Exception):
    """Exception raised when API request input parameters fail validation checks."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
