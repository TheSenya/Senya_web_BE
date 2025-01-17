class BaseError(Exception):
    """Base exception class for all application-specific exceptions."""
    
    def __init__(self, message: str = "An unexpected error occurred", code: int = 500):
        """
        Initialize the base error.
        
        Args:
            message (str): Human-readable error message
            code (int): HTTP status code or custom error code
        """
        self.message = message
        self.code = code
        super().__init__(self.message)