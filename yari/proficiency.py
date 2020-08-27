from yari.loader import _read


class ProficiencyGenerator:
    """
    Merges class with racial proficiencies (if applicable).

    :param str proficiency_type: Proficiency type (armors|tools|weapons).
    :param list class_proficiency: Class based proficiency by proficiency_type.
    :param list race_proficiency: Race based proficiency by proficiency_type (if applicable).

    """

    def __init__(
        self, proficiency_type: str, class_proficiency: list, race_proficiency: list
    ) -> None:
        if proficiency_type not in ("armors", "tools", "weapons"):
            raise ValueError(
                f"Invalid 'proficiency_type' argument '{proficiency_type}' specified."
            )

        race_proficiency = [p for p in race_proficiency if p not in class_proficiency]
        if len(race_proficiency) is not 0:
            self.proficiency = class_proficiency + race_proficiency
        else:
            self.proficiency = class_proficiency


def get_armor_chest():
    """Returns a full collection of armors."""
    armor_chest = dict()
    for armor_category in ("Heavy", "Light", "Medium"):
        armor_chest[armor_category] = [p for p in _read(armor_category, file="armors")][0]
    yield armor_chest


def get_tool_chest():
    """Returns a full collection of tools."""
    for main_tool in _read(file="tools"):
        if main_tool in ("Artisan's tools", "Gaming set", "Musical instrument"):
            for sub_tool in [t for t in _read(main_tool, file="tools")][0]:
                yield f"{main_tool} - {sub_tool}"
        else:
            yield main_tool


def get_weapon_chest():
    """Returns a full collection of weapons."""
    weapon_chest = dict()
    for weapon_category in ("Simple", "Martial"):
        weapon_chest[weapon_category] = [w for w in _read(weapon_category, file="weapons")][0]
    yield weapon_chest
