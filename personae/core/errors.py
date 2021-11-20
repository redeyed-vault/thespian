class Error(Exception):
    """Handles general exceptions."""


class AbilityScoreImprovementError(Error):
    """Handles ability score improvement errors."""


class AnthropometricCalculatorError(Error):
    """Handles anthropometric calculator errors."""


class BlueprintError(Error):
    """Handles an invalid seamstress error."""


class DieArgumentError(ValueError):
    """Handles an invalid die rolling argument."""


class FlagParserError(Error):
    """Handles an invalid flag format error."""


class SeamstressError(Error):
    """Handles an invalid seamstress error."""
