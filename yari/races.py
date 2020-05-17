import random

from yari.collect import purge
from yari.reader import reader


class _Races:
    """DO NOT call class directly. Used to generate racial traits.
    Based on the inheriting class.

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

    def __init__(self, **kw) -> None:
        self.race = self.__class__.__name__
        """
            Args:
                kw:
                    - class_attr (dict): Characters's chosen class' primary abilities.
                    - subrace (str): Character's chosen subrace (if any).
                    - variant (bool): Use variant rules.
        """

        if self.race == "_Races":
            raise Exception("this class must be inherited")

        if "class_attr" not in kw and not isinstance(kw.get("class_attr"), dict):
            kw["class_attr"] = None
        if "subrace" not in kw:
            kw["subrace"] = None
        if "variant" not in kw or not isinstance(kw.get("variant"), bool):
            kw["variant"] = False

        self.class_attr = tuple(kw.get("class_attr").values())
        self.subrace = kw.get("subrace")
        self.variant = kw.get("variant")

        self.traits = reader("races", (self.race, "traits"))
        self.traits["skills"] = list()

        # Dragonborn character's get draconic ancestry.
        if self.race == "Dragonborn":
            draconic_ancestry = reader("races", (self.race, "traits", "ancestry"))
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

            breath_weapon = damage_resistance
            self.traits["ancestry"] = draconic_ancestry
            self.traits["breath"] = breath_weapon
            self.traits["resistance"] = [damage_resistance]

        # Dwarves get a random tool proficiency.
        if self.race == "Dwarf":
            tool_bonus = random.choice(self.traits.get("proficiency").get("tools"))
            self.traits["proficiency"]["tools"] = [tool_bonus]

        # Elves and HalfOrcs get a specific bonus skill.
        if self.race in ("Elf", "HalfOrc",):
            if self.race == "Elf":
                self.traits["skills"] = ["Perception"]
            elif self.race == "HalfOrc":
                self.traits["skills"] = ["Intimidation"]

        # Bonus languages for Half-Elf, Human or High Elf.
        if self.race in ("HalfElf", "Human") or self.subrace == "High":
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

        # Bonus skills for HalfElf and Human variants.
        if self.race == "Human" and self.variant or self.race == "HalfElf":
            all_skills = reader("races", (self.race, "traits", "skills"))
            if self.race == "HalfElf":
                self.traits["skills"] = random.sample(all_skills, 2)
            elif self.race == "Human":
                self.traits["skills"] = random.sample(all_skills, 1)

        # Human variants only have two bonus "racial" abilities.
        if self.race == "Human" and self.variant:
            if self.class_attr is not None:
                bonus_abilities = dict()
                for ability in self.class_attr:
                    bonus_abilities[ability] = 1
                self.traits["abilities"] = bonus_abilities

        if self.subrace is None:
            return
        else:
            subrace_traits = reader("subraces", (self.subrace, "traits"))
            self.traits = self._merge_traits(self.traits, subrace_traits)

    @staticmethod
    def _merge_traits(base_traits: dict, sub_traits: dict) -> dict:
        """Combines racial and subracial traits if applicable.

        Args:
            base_traits (dict): Dict of base racial traits.
            sub_traits (dict): Dict of sub racial traits (if applicable).
        """
        for trait, value in sub_traits.items():
            # No proficiency key index in base traits, add it.
            if trait not in base_traits:
                base_traits[trait] = {}

            if trait == "abilities":
                for ability, bonus in value.items():
                    base_traits[trait][ability] = bonus

            if trait == "cantrip":
                cantrip_list = reader("subraces", ("High", "traits", "cantrip"))
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
                for element in value:
                    base_traits.get(trait).append(element)
                base_traits[trait].sort()

            if trait == "magic" or trait == "sensitivity" or trait == "toughness":
                base_traits[trait] = sub_traits.get(trait)

            if trait == "proficiency":
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
    def __init__(self, **kw) -> None:
        super(Aasimar, self).__init__(**kw)


class Dragonborn(_Races):
    def __init__(self, **kw) -> None:
        super(Dragonborn, self).__init__(**kw)


class Dwarf(_Races):
    def __init__(self, **kw) -> None:
        super(Dwarf, self).__init__(**kw)


class Elf(_Races):
    def __init__(self, **kw) -> None:
        super(Elf, self).__init__(**kw)


class Gnome(_Races):
    def __init__(self, **kw) -> None:
        super(Gnome, self).__init__(**kw)


class HalfElf(_Races):
    def __init__(self, **kw) -> None:
        super(HalfElf, self).__init__(**kw)


class HalfOrc(_Races):
    def __init__(self, **kw) -> None:
        super(HalfOrc, self).__init__(**kw)


class Halfling(_Races):
    def __init__(self, **kw) -> None:
        super(Halfling, self).__init__(**kw)


class Human(_Races):
    def __init__(self, **kw) -> None:
        super(Human, self).__init__(**kw)


class Tiefling(_Races):
    def __init__(self, **kw) -> None:
        super(Tiefling, self).__init__(**kw)


def get_subraces_by_race(race: str) -> tuple:
    """Returns a list of valid subraces by race.

    Args:
        race (str): Race to retrieve subraces for.
    """
    valid_subraces = list()
    for name, traits in reader("subraces").items():
        if traits.get("parent") == race:
            valid_subraces.append(name)
    return tuple(valid_subraces)
