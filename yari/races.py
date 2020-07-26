import random

from yari.exceptions import InheritanceError, InvalidValueError
from yari.loader import _read
from yari.ratio import RatioGenerator


class _Races:
    """DO NOT call class directly. Used to generate racial traits.

        Inherited by the following classes:

            - Aasimar
            - Dragonborn
            - Dwarf
            - Elf
            - Gith
            - Gnome
            - HalfElf
            - HalfOrc
            - Halfling
            - Human
            - Tiefling

    """

    def __init__(self, subrace: str, sex: str, level: int) -> None:
        """
            Args:
                subrace (str): Character's chosen subrace (if applicable).
                sex (str): Characters's chosen gender.
                level (int): Character's chosen level.

        """
        self.race = self.__class__.__name__
        if self.race == "_Races":
            raise InheritanceError("This class must be inherited")

        if subrace != "" and subrace not in get_subraces_by_race(self.race):
            raise InvalidValueError(f"Argument 'subrace' value '{subrace}' is invalid.")
        elif (
            len([get_subraces_by_race(self.race)]) is not 0
            and subrace is None
            or subrace == ""
        ):
            raise InvalidValueError(
                f"Argument 'subrace' is required for '{self.race}'."
            )
        else:
            self.subrace = subrace

        if sex not in ("Female", "Male",):
            raise InvalidValueError(
                f"Argument 'sex' value must be either 'Female|Male'."
            )
        else:
            self.sex = sex

        if not isinstance(level, int):
            raise InvalidValueError("Argument 'level' value must be of type 'int'.")
        else:
            self.level = level

        # Retrieve racial/subracial traits (if applicable).
        self.all = _read(self.race, file="races")
        if self.subrace != "":
            subrace_traits = _read(self.subrace, file="subraces")
            self._merge_traits(subrace_traits)

        self._add_ability_traits()
        self._add_ancestry_traits()
        self._add_cantrip_traits()
        self._add_language_traits()
        self._add_other_traits()
        self._add_ratio_traits()
        self._add_skill_traits()

        self.all["other"] = [tuple(x) for x in self.all["other"]]
        self.bonus = self.all.get("bonus")
        self.languages = self.all.get("languages")
        self.other = self.all.get("other")
        self.size = self.all.get("size")
        self.speed = self.all.get("speed")

    def __repr__(self):
        if self.subrace != "":
            return '<{} subrace="{}" sex="{}" level="{}">'.format(
                self.race, self.subrace, self.sex, self.level
            )
        else:
            return '<{} sex="{}" level="{}">'.format(self.race, self.sex, self.level)

    def _add_ability_traits(self):
        """Add HalfElf, Human "racial" ability traits."""
        if self.race == "HalfElf":
            valid_abilities = [
                "Strength",
                "Dexterity",
                "Constitution",
                "Intelligence",
                "Wisdom",
            ]
            valid_abilities = random.sample(valid_abilities, 2)
            for ability in valid_abilities:
                self.all["bonus"][ability] = 1

    def _add_ancestry_traits(self):
        """Add Dragonborn character ancestry traits."""
        if self.race != "Dragonborn":
            return

        for trait, value in self.all.items():
            if trait == "other":
                for index, feature in enumerate(value):
                    if "Draconic Ancestry" in feature:
                        draconic_ancestor = random.choice(feature[1])
                        self.all[trait][index] = [feature[0], draconic_ancestor]

                        damage_resistance = None
                        if draconic_ancestor in ("Black", "Copper",):
                            damage_resistance = "Acid"
                        elif draconic_ancestor in ("Blue", "Bronze",):
                            damage_resistance = "Lightning"
                        elif draconic_ancestor in ("Brass", "Gold", "Red",):
                            damage_resistance = "Fire"
                        elif draconic_ancestor == "Green":
                            damage_resistance = "Poison"
                        elif draconic_ancestor in ("Silver", "White"):
                            damage_resistance = "Cold"
                        self.all[trait].append(["Breath Weapon", [damage_resistance]])
                        self.all[trait].append(
                            ["Damage Resistance", [damage_resistance]]
                        )

    def _add_cantrip_traits(self):
        """Add HighElf, or Forest Gnome bonus cantrips."""
        for trait, value in self.all.items():
            if trait == "other":
                if self.subrace == "Forest":
                    pass
                elif self.subrace == "High":
                    for index, feature in enumerate(value):
                        if "Cantrip" in feature:
                            self.all[trait][index] = (
                                feature[0],
                                random.choice(feature[1]),
                            )

    def _add_language_traits(self):
        """Add Githyanki, Half-Elf, Human or High Elf character language traits."""
        if self.race not in ("HalfElf", "Human") and self.subrace not in (
            "Githyanki",
            "High",
        ):
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
            standard_languages = [
                language
                for language in standard_languages
                if language not in self.all.get("languages")
            ]
            self.all["languages"].append(random.choice(standard_languages))

    def _add_other_traits(self):
        """Add Elf, Dwarf and Githyanki bonus proficiencies."""
        self.armors = self.tools = self.weapons = self.magic = list()

        for trait, value in self.all.items():
            if trait == "other":
                for index, feature in enumerate(value):
                    if (
                        "Martial Prodigy (Armor)" in feature
                        or "Dwarven Armor Training" in feature
                    ):
                        self.armors = feature[1]
                    elif "Tool Proficiency" in feature:
                        tool_choice = [random.choice(feature[1])]
                        self.all[trait][index] = [feature[0], tool_choice]
                        self.tools = tool_choice
                    elif (
                        "Drow Weapon Training" in feature
                        or "Dwarven Combat Training" in feature
                        or "Elf Weapon Training" in feature
                        or "Martial Prodigy (Weapon)" in feature
                    ):
                        self.weapons = feature[1]
                    elif (
                        "Drow Magic" in feature
                        or "Duergar Magic" in feature
                        or "Githyanki Psionics" in feature
                        or "Githzerai Psionics" in feature
                        or "Infernal Legacy" in feature
                        or "Legacy of Avernus" in feature
                        or "Legacy of Cania" in feature
                        or "Legacy of Dis" in feature
                        or "Legacy of Maladomini" in feature
                        or "Legacy of Malbolge" in feature
                        or "Legacy of Minauros" in feature
                        or "Legacy of Phlegethos" in feature
                        or "Legacy of Stygia" in feature
                    ):
                        spells = [
                            row
                            for key, row in enumerate(feature[1])
                            if self.level >= row[0]
                        ]
                        spells = [tuple(sp) for sp in spells]
                        self.all[trait][index] = (feature[0], spells)
                        self.magic = spells

    def _add_ratio_traits(self):
        (height, weight) = RatioGenerator(self.race, self.subrace, self.sex).calculate()
        self.all["size"] = (self.all.get("size"), height, weight)
        del self.all["ratio"]

    def _add_skill_traits(self):
        """Add Elf Keen Senses, HalfOrc Menacing and HalfElf Skill Affinity skill bonuses."""
        self.skills = []

        for trait, value in self.all.items():
            if trait == "other":
                for index, feature in enumerate(value):
                    if "Keen Senses" in feature or "Menacing" in feature:
                        self.skills = feature[1]
                    elif "Skill Versatility" in feature:
                        skills = random.sample(feature[1], 2)
                        self.all[trait][index] = (feature[0], skills)
                        self.skills = skills

    def _merge_traits(self, sub_traits: dict):
        """Combines racial and subracial traits (if applicable).

        Args:
            sub_traits (dict): Dictionary of sub-racial traits (if applicable).

        """
        for trait, value in sub_traits.items():
            if trait not in self.all:
                self.all[trait] = sub_traits[trait]
            elif trait == "bonus":
                for ability, bonus in value.items():
                    self.all[trait][ability] = bonus
            elif trait == "languages":
                for language in sub_traits.get(trait):
                    self.all.get(trait).append(language)
                self.all[trait].sort()
            elif trait == "other":
                for other in sub_traits.get(trait):
                    self.all.get(trait).append(other)


class Aasimar(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Aasimar, self).__init__(subrace, sex, level)


class Dragonborn(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Dragonborn, self).__init__(subrace, sex, level)


class Dwarf(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Dwarf, self).__init__(subrace, sex, level)


class Elf(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Elf, self).__init__(subrace, sex, level)


class Gith(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Gith, self).__init__(subrace, sex, level)


class Gnome(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Gnome, self).__init__(subrace, sex, level)


class HalfElf(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(HalfElf, self).__init__(subrace, sex, level)


class HalfOrc(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(HalfOrc, self).__init__(subrace, sex, level)


class Halfling(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Halfling, self).__init__(subrace, sex, level)


class Human(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Human, self).__init__(subrace, sex, level)


class Tiefling(_Races):
    def __init__(self, subrace, sex, level) -> None:
        super(Tiefling, self).__init__(subrace, sex, level)


def get_subraces_by_race(race: str):
    """Yields a list of valid subraces by race.

    Args:
        race (str): Race to retrieve subraces for.

    """
    for subrace in _read(file="subraces"):
        if _read(subrace, "parent", file="subraces") == race:
            yield subrace


"""
r = Elf("Drow", "Female", 4)
print(r)
print(r.all)
print(r.bonus)
print(r.languages)
print(r.other)
print(r.magic)
print(r.size)
print(r.speed)
print(r.armors)
print(r.tools)
print(r.weapons)
print(r.skills)
"""
