class Error(Exception):
    """Handles general exceptions."""


class AbilityScoreImprovementError(Error):
    """Handles ability score improvement errors."""


class AnthropometricCalculatorError(Error):
    """Handles anthropometric calculator errors."""


class DieArgumentError(ValueError):
    """Handles an invalid die rolling argument."""


class FlagParserError(Error):
    """Handles an invalid flag format error."""
