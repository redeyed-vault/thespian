class ProficiencyTypeValueError(ValueError):
    """Raised if invalid proficiency type specified."""


class ProficiencyGenerator:
    """Merges class with racial proficiencies (if applicable)."""

    def __init__(
        self, prof_type: str, class_proficiency: list, race_proficiency: list
    ) -> None:
        """
        Args:
            prof_type (str): Proficiency type (armors|tools|weapons).
            class_proficiency (list): Class based proficiency by prof_type.
            race_proficiency (list): Race based proficiency by prof_type (if applicable).
        """
        if prof_type not in ("armors", "tools", "weapons"):
            raise ProficiencyTypeValueError(
                f"Invalid 'prof_type' argument '{prof_type}' specified."
            )

        self.proficiency = class_proficiency + race_proficiency
