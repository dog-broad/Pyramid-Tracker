class PyramidTrackerError(Exception):
    """Base exception for the application"""
    pass

class ConfigError(PyramidTrackerError):
    """Configuration related errors"""
    pass

class ScraperError(PyramidTrackerError):
    """Base class for scraper errors"""
    pass

class RateLimitError(ScraperError):
    """Rate limit exceeded"""
    pass

class AuthenticationError(ScraperError):
    """Authentication failed"""
    pass

class UserNotFoundError(ScraperError):
    """User not found"""
    pass

class DatabaseError(PyramidTrackerError):
    """Database operation errors"""
    pass

class DatabaseDoesNotExistError(DatabaseError):
    """Database does not exist"""
    pass