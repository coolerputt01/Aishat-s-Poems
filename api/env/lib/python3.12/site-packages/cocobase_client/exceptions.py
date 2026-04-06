class CocobaseError(Exception):
    """Base class for all Cocobase client errors."""
    pass
class InvalidApiKeyError(CocobaseError):
    """Raised when the provided API key is invalid."""
    def __init__(self, message="Invalid API key provided."):
        super().__init__(message)