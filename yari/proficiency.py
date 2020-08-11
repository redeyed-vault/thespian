from yari.loader import _read


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

        race_proficiency = [p for p in race_proficiency if p not in class_proficiency]
        if len(race_proficiency) is not 0:
            self.proficiency = class_proficiency + race_proficiency
        else:
            self.proficiency = class_proficiency


def get_armor_chest():
    """Returns a full collection of armors."""
    pass


def get_tool_chest():
    """Returns a full collection of tools."""
    for main_tool in _read(file="tools"):
        if main_tool in ("Artisan's tools", "Gaming set", "Musical instrument"):
            for sub_tool in _read(main_tool, file="tools"):
                yield f"{main_tool} - {sub_tool}"
        else:
            yield main_tool


def get_weapon_chest():
    """Returns a full collection of weapons."""
    weapon_chest = dict()
    for weapon_category in ("Simple", "Martial"):
        weapon_chest[weapon_category] = _read(weapon_category, file="weapons")
    yield weapon_chest
