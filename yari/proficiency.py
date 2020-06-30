from yari.collect import fuse


class ProficiencyTypeValueError(ValueError):
    """Raised if invalid proficiency type specified."""


class ProficiencyGenerator:
    """Merges class with racial proficiencies (if applicable)."""

    def __init__(self, prof_type: str, features: dict, traits: dict) -> None:
        """
        Args:
            prof_type (str): Proficiency type (armors|tools|weapons).
            features (dict): Class proficiency by prof_type.
            traits (dict): Racial proficiency by prof_type (if applicable).
        """
        if prof_type not in ("armors", "tools", "weapons"):
            raise ProficiencyTypeValueError(
                f"invalid 'prof_type' argument '{prof_type}'"
            )
        else:
            class_proficiency = features.get("proficiency").get(prof_type)
            if "proficiency" in traits:
                trait_proficiency = traits.get("proficiency")
                if prof_type in trait_proficiency:
                    trait_proficiency = trait_proficiency.get(prof_type)
                    fuse(class_proficiency, trait_proficiency)
            self.proficiency = class_proficiency
