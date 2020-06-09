import random

from yari.collect import purge
from yari.reader import reader


class RacesInheritError(Exception):
    """Generic _Races inheritance error."""


class RacesValueError(ValueError):
    """Raised for _Races ValueError occurrences."""


class _Races:
    """DO NOT call class directly. Used to generate racial traits.
        Inherited by the following classes:

        - Aasimar
        - Dragonborn
        - Dwarf
        - Elf
        - Gnome
        - HalfElf
        - HalfOrc
        - Halfling
        - Human
        - Tiefling

    """

    def __init__(self, subrace: (None, str), class_attr: dict, variant: bool) -> None:
        """
            Args:
                subrace (str): Character's chosen subrace (if applicable).
                class_attr (dict): Characters's chosen class' primary abilities.
                variant (bool): Use variant rules (Human only).

        """
        self.race = self.__class__.__name__
        if self.race == "_Races":
            raise RacesInheritError("this class must be inherited")

        if subrace is not None and not get_subraces_by_race(self.race):
            raise RacesValueError(f"invalid subrace '{subrace}'")
        else:
            self.subrace = subrace

        if not isinstance(class_attr, dict):
            raise RacesValueError("class_attr value must be of type 'dict'")
        else:
            self.class_attr = tuple(class_attr.values())

        if not isinstance(variant, bool):
            raise RacesValueError("variant value must be of type 'bool'")
        else:
            self.variant = variant

        self.traits = reader("races", (self.race,)).get("traits")
        self._add_ability_traits()
        self._add_ancestry_traits()
        self._add_language_traits()
        self._add_skill_traits()

        # Dwarves get a random tool proficiency.
        if self.race == "Dwarf":
            tool_bonus = random.choice(self.traits.get("proficiency").get("tools"))
            self.traits["proficiency"]["tools"] = [tool_bonus]

        # Merge racial and subracial traits (if applicable).
        if self.subrace != "":
            subrace_traits = reader("subraces", (self.subrace,)).get("traits")
            self.traits = self._merge_traits(self.traits, subrace_traits)

    def _add_ability_traits(self):
        """Add HalfElf, Human "racial" ability traits."""
        if self.race == "HalfElf":
            if "Charisma" in self.class_attr:
                self.class_attr = list(self.class_attr)
                self.class_attr.remove("Charisma")
                ability = self.class_attr[0]
            else:
                ability = random.choice(self.class_attr)

            self.traits["abilities"][ability] = 1
        elif self.race == "Human" and self.variant:
            bonus_abilities = dict()
            for ability in self.class_attr:
                bonus_abilities[ability] = 1
            self.traits["abilities"] = bonus_abilities

    def _add_ancestry_traits(self):
        """Add Dragonborn character ancestry traits."""
        if self.race != "Dragonborn":
            return
        else:
            draconic_ancestry = (
                reader("races", (self.race,)).get("traits").get("ancestry")
            )
            draconic_ancestry = random.choice(draconic_ancestry)
            damage_resistance = None
            if draconic_ancestry in ("Black", "Copper",):
                damage_resistance = "Acid"
            elif draconic_ancestry in ("Blue", "Bronze",):
                damage_resistance = "Lightning"
            elif draconic_ancestry in ("Brass", "Gold", "Red",):
                damage_resistance = "Fire"
            elif draconic_ancestry == "Green":
                damage_resistance = "Poison"
            elif draconic_ancestry in ("Silver", "White"):
                damage_resistance = "Cold"

            self.traits["ancestry"] = draconic_ancestry
            self.traits["breath"] = damage_resistance
            self.traits["resistance"] = [damage_resistance]

    def _add_language_traits(self):
        """Add Half-Elf, Human or High Elf character language traits."""
        if self.race not in ("HalfElf", "Human") or self.subrace != "High":
            return
        else:
            standard_languages = [
                "Common",
                "Dwarvish",
                "Elvish",
                "Giant",
                "Gnomish",
                "Goblin",
                "Halfling",
                "Orc",
            ]
            purge(standard_languages, self.traits.get("languages"))
            self.traits["languages"].append(random.choice(standard_languages))

    def _add_skill_traits(self):
        """Add Elf, HalfOrcs, HighElf or Human character skill traits."""
        self.traits["skills"] = list()
        if self.race in ("Elf", "HalfOrc",):
            if self.race == "Elf":
                self.traits["skills"] = ["Perception"]
            elif self.race == "HalfOrc":
                self.traits["skills"] = ["Intimidation"]
        elif self.race == "Human" and self.variant or self.race == "HalfElf":
            all_skills = reader("races", (self.race,)).get("traits").get("skills")
            if self.race == "HalfElf":
                self.traits["skills"] = random.sample(all_skills, 2)
            elif self.race == "Human":
                self.traits["skills"] = random.sample(all_skills, 1)

    @staticmethod
    def _merge_traits(base_traits: dict, sub_traits: dict) -> dict:
        """Combines racial and subracial traits (if applicable).

        Args:
            base_traits (dict): Dictionary of base racial traits.
            sub_traits (dict): Dictionary of sub-racial traits (if applicable).

        """
        for trait, value in sub_traits.items():
            # No trait key index in base_traits, add it.
            if trait not in base_traits:
                base_traits[trait] = None

            if trait == "abilities":
                for ability, bonus in value.items():
                    base_traits[trait][ability] = bonus

            if trait == "cantrip":
                cantrip_list = (
                    reader("subraces", ("High",)).get("traits").get("cantrip")
                )
                bonus_cantrip = [random.choice(cantrip_list)]
                base_traits[trait] = bonus_cantrip

            if trait == "darkvision":
                if sub_traits.get(trait) > base_traits.get(trait):
                    base_traits[trait] = sub_traits.get(trait)

            if trait == "languages":
                for language in sub_traits.get(trait):
                    base_traits.get(trait).append(language)
                base_traits[trait].sort()

            if trait == "resistance":
                if base_traits[trait] is None:
                    base_traits[trait] = list()

                for element in value:
                    base_traits.get(trait).append(element)
                base_traits[trait].sort()

            if trait == "magic" or trait == "sensitivity" or trait == "toughness":
                base_traits[trait] = sub_traits.get(trait)

            if trait == "proficiency":
                if base_traits[trait] is None:
                    base_traits[trait] = dict()

                for proficiency_type in list(sub_traits[trait].keys()):
                    if proficiency_type == "armors":
                        base_traits[trait].update(armors=sub_traits[trait]["armors"])

                    if proficiency_type == "tools":
                        base_traits[trait].update(tools=sub_traits[trait]["tools"])

                    if proficiency_type == "weapons":
                        base_traits[trait].update(weapons=sub_traits[trait]["weapons"])

            if trait == "tinker":
                base_traits[trait] = sub_traits.get(trait)
        return base_traits


class Aasimar(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(Aasimar, self).__init__(subrace, class_attr, variant)


class Dragonborn(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(Dragonborn, self).__init__(subrace, class_attr, variant)


class Dwarf(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(Dwarf, self).__init__(subrace, class_attr, variant)


class Elf(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(Elf, self).__init__(subrace, class_attr, variant)


class Gnome(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(Gnome, self).__init__(subrace, class_attr, variant)


class HalfElf(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(HalfElf, self).__init__(subrace, class_attr, variant)


class HalfOrc(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(HalfOrc, self).__init__(subrace, class_attr, variant)


class Halfling(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(Halfling, self).__init__(subrace, class_attr, variant)


class Human(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(Human, self).__init__(subrace, class_attr, variant)


class Tiefling(_Races):
    def __init__(self, subrace, class_attr, variant) -> None:
        super(Tiefling, self).__init__(subrace, class_attr, variant)


def get_subraces_by_race(race: str):
    """Yields a list of valid subraces by race.

    Args:
        race (str): Race to retrieve subraces for.

    """
    for subrace in reader("subraces"):
        parent = reader("subraces", (subrace,))
        if parent.get("parent") == race:
            yield subrace
