class InheritanceError(Exception):
    """Generic inheritance class error."""


class InvalidValueError(ValueError):
    """Raised for inherited invalid ValueError errors."""


class RatioValueError(InvalidValueError):
    """Raised for invalid ratio value errors."""
