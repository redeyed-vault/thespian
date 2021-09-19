class Error(Exception):
    """Handles general Personae exceptions."""
    pass


class DieArgumentError(ValueError):
    """Handles an invalid die rolling argument."""
