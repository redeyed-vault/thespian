import math
import random

from yari.dice import roll
from yari.loader import load


ALLOWED_PC_GENDERS = ("Female", "Male")
ALLOWED_PC_RACES = load(file="races")
ALLOWED_PC_SUBRACES = load(file="subraces")


class _Races:
    """
    DO NOT call class directly. Used to generate racial traits.

    Inherited by the following classes:

        - Aasimar
        - Bugbear
        - Dragonborn
        - Dwarf
        - Elf
        - Firbolg
        - Gith
        - Gnome
        - Goblin
        - Goliath
        - HalfElf
        - HalfOrc
        - Halfling
        - Hobgoblin
        - Human
        - Kenku
        - Kobold
        - Lizardfolk
        - Orc
        - Tabaxi
        - Tiefling
        - Triton
        - Yuan-ti

    :param str sex: Character's chosen gender.
    :param str subrace: Character's chosen subrace (if applicable).
    :param int level: Character's chosen level.

    """

    def __init__(self, sex: str, subrace: str = "", level: int = 1) -> None:
        self.race = self.__class__.__name__
        valid_subraces = [
            sr for sr in get_subraces_by_race(ALLOWED_PC_SUBRACES, self.race)
        ]

        if self.race == "_Races":
            raise Exception(
                "This class must be inherited to use. It is currently used by "
                "the Aasimar, Bugbear, Dragonborn, Dwarf, Elf, Firbolg, Gith, "
                "Gnome, Goblin, Goliath, HalfElf, HalfOrc, Halfling, Hobgoblin, "
                "Human, Kenku, Kobold, Lizardfolk, Orc, Tabaxi, Tiefling, "
                "Triton, and Yuanti 'race' classes."
            )

        if sex in (
            "Female",
            "Male",
        ):
            self.sex = sex
        else:
            raise ValueError(f"Argument 'sex' value must be 'Male' or 'Female'.")

        if not has_subraces(self.race):
            self.subrace = ""
        else:
            if subrace not in valid_subraces:
                raise ValueError(
                    f"Argument 'subrace' value '{subrace}' is invalid for '{self.race}'."
                )
            elif len(valid_subraces) != 0 and subrace == "":
                raise ValueError(f"Argument 'subrace' is required for '{self.race}'.")
            else:
                self.subrace = subrace

        if not isinstance(level, int):
            raise ValueError("Argument 'level' value must be of type 'int'.")
        else:
            self.level = level

        # Get racial traits and merge with subracial traits (if ANY).
        self.all = load(self.race, file="races")
        if self.subrace != "":
            subrace_traits = load(self.subrace, file="subraces")
            for trait, value in subrace_traits.items():
                if trait not in self.all:
                    self.all[trait] = subrace_traits[trait]
                elif trait == "bonus":
                    for ability, bonus in value.items():
                        self.all[trait][ability] = bonus
                elif trait == "languages":
                    for language in subrace_traits.get(trait):
                        self.all.get(trait).append(language)
                    self.all[trait].sort()
                elif trait == "other":
                    for other in subrace_traits.get(trait):
                        self.all[trait].append(other)
                elif trait == "ratio":
                    self.all[trait] = subrace_traits.get(trait)

        self._add_race_ability_bonus()
        self._add_race_ancestry()
        self._add_race_cantrip_bonus()
        self._add_race_language_bonus()
        self._add_race_traits()
        self._add_race_mass()
        self._add_race_skill_bonus()
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

    def _add_race_ability_bonus(self):
        """Add HalfElf racial ability bonuses."""
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

    def _add_race_ancestry(self):
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
                        if draconic_ancestor in (
                            "Black",
                            "Copper",
                        ):
                            damage_resistance = "Acid"
                        elif draconic_ancestor in (
                            "Blue",
                            "Bronze",
                        ):
                            damage_resistance = "Lightning"
                        elif draconic_ancestor in (
                            "Brass",
                            "Gold",
                            "Red",
                        ):
                            damage_resistance = "Fire"
                        elif draconic_ancestor == "Green":
                            damage_resistance = "Poison"
                        elif draconic_ancestor in ("Silver", "White"):
                            damage_resistance = "Cold"
                        self.all[trait].append(["Breath Weapon", [damage_resistance]])
                        self.all[trait].append(
                            ["Damage Resistance", [damage_resistance]]
                        )

    def _add_race_cantrip_bonus(self):
        """Add High Elf, or Forest Gnome bonus cantrips."""
        if self.race == "Yuanti" or self.subrace in ("Forest", "High"):
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

    def _add_race_language_bonus(self):
        """
        Add any racial bonus languages.

            Githyanki
            Half-Elf
            High Elf
            Human
            Tabaxi

        """
        if self.race not in ("HalfElf", "Human", "Tabaxi") and self.subrace not in (
            "Githyanki",
            "High",
        ):
            return

        if self.subrace == "Githyanki":
            for trait, value in self.all.items():
                if trait == "other":
                    for index, feature in enumerate(value):
                        if "Decadent Mastery" in feature:
                            decadent_language = random.choice(feature[1])
                            self.all[trait][index] = (
                                feature[0],
                                decadent_language,
                            )
                            self.all["languages"].append(decadent_language)
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

    def _add_race_mass(self):
        """Generates a character's height & weight."""
        height_base = self.all.get("ratio").get("height").get("base")
        height_modifier = self.all.get("ratio").get("height").get("modifier")
        height_modifier = sum(list(roll(height_modifier)))
        inches = height_base + height_modifier
        feet = math.floor(inches / 12)
        inches = inches % 12
        height = "{}' {}\"".format(feet, inches)

        weight_base = self.all.get("ratio").get("weight").get("base")
        weight_modifier = self.all.get("ratio").get("weight").get("modifier")
        weight_modifier = sum(list(roll(weight_modifier)))
        weight = (height_modifier * weight_modifier) + weight_base
        weight = f"{weight} lbs."

        self.all["size"] = "{} size ({}, {})".format(
            self.all.get("size"), height, weight
        )

        del self.all["ratio"]

    def _add_race_traits(self):
        """
        Add all bonus armor, tool, and/or weapon proficiencies, and other traits.

            - Aasimar = Necrotic Shield, Radiant Consumption/Soul
            - Drow = Drow Magic, Drow Weapon Training
            - Duergar = Duergar Magic
            - Dwarf = Dwarven Armor Training, Dwarven Combat Training, Tool Proficiency
            - Elf = Elven Combat Training
            - Githyanki = Githyanki Psionics, Martial Training
            - Githzerai = Githzerai Psionics
            - Hobgoblin = Martial Prodigy
            - Tiefling = Infernal Legacy, Legacy powers
            - Yuanti = Innate Spellcasting

        """
        self.armors = self.tools = self.weapons = self.magic = list()
        for trait, value in self.all.items():
            if trait == "other":
                for index, feature in enumerate(value):
                    if (
                        "Dwarven Armor Training" in feature
                        or "Martial Prodigy (Armor)" in feature
                        or "Martial Training (Armor)" in feature
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
                        or "Sea Elf Training" in feature
                    ):
                        self.weapons = feature[1]
                    elif (
                        "Drow Magic" in feature
                        or "Duergar Magic" in feature
                        or "Githyanki Psionics" in feature
                        or "Githzerai Psionics" in feature
                        or "Infernal Legacy" in feature
                        or "Innate Spellcasting" in feature
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
                    elif "Martial Training (Weapon)" in feature:
                        self.weapons = random.sample(feature[1], 2)
                        self.all[trait][index] = (feature[0], self.weapons)

    def _add_race_skill_bonus(self):
        """
        Applies racial bonus skills (if ANY).

            - Bugbear = Sneaky - Stealthy
            - Elf = Keen Senses - Perception
            - Goliath = Natural Athlete - Athlete
            - HalfOrc/Orc = Menacing - Intimidation
            - HalfElf = Skill Affinity bonus skills
            - Kenku = Kenku Training bonus skills
            - Lizardfolk = Hunter's Lore bonus skills
            - Tabaxi = Cat's Talent - Perception

        """
        self.skills = list()
        for trait, value in self.all.items():
            if trait == "other":
                for index, feature in enumerate(value):
                    if (
                        "Cat's Talent" in feature
                        or "Keen Senses" in feature
                        or "Menacing" in feature
                        or "Natural Athlete" in feature
                        or "Sneaky" in feature
                    ):
                        self.skills = feature[1]
                    elif (
                        "Hunter's Lore" in feature
                        or "Kenku Training" in feature
                        or "Skill Versatility" in feature
                    ):
                        skills = random.sample(feature[1], 2)
                        self.all[trait][index] = (feature[0], skills)
                        self.skills = skills


class Aasimar(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Aasimar, self).__init__(sex, subrace, level)


class Bugbear(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Bugbear, self).__init__(sex, subrace, level)


class Dragonborn(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Dragonborn, self).__init__(sex, subrace, level)


class Dwarf(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Dwarf, self).__init__(sex, subrace, level)


class Elf(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Elf, self).__init__(sex, subrace, level)


class Firbolg(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Firbolg, self).__init__(sex, subrace, level)


class Gith(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Gith, self).__init__(sex, subrace, level)


class Gnome(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Gnome, self).__init__(sex, subrace, level)


class Goblin(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Goblin, self).__init__(sex, subrace, level)


class Goliath(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Goliath, self).__init__(sex, subrace, level)


class HalfElf(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(HalfElf, self).__init__(sex, subrace, level)


class HalfOrc(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(HalfOrc, self).__init__(sex, subrace, level)


class Halfling(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Halfling, self).__init__(sex, subrace, level)


class Hobgoblin(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Hobgoblin, self).__init__(sex, subrace, level)


class Human(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Human, self).__init__(sex, subrace, level)


class Kenku(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Kenku, self).__init__(sex, subrace, level)


class Kobold(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Kobold, self).__init__(sex, subrace, level)


class Lizardfolk(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Lizardfolk, self).__init__(sex, subrace, level)


class Orc(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Orc, self).__init__(sex, subrace, level)


class Tabaxi(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Tabaxi, self).__init__(sex, subrace, level)


class Tiefling(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Tiefling, self).__init__(sex, subrace, level)


class Triton(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Triton, self).__init__(sex, subrace, level)


class Yuanti(_Races):
    def __init__(self, sex, subrace, level) -> None:
        super(Yuanti, self).__init__(sex, subrace, level)


def get_subraces_by_race(allowed_subraces: list, race: str):
    """Yields a list of valid subraces by race.

    :param list allowed_subraces: List of allowed subraces.
    :param str race: Race to retrieve subraces for.

    """
    for subrace in allowed_subraces:
        if load(subrace, "parent", file="subraces") == race:
            yield subrace


def has_subraces(race: str) -> bool:
    """
    Determines if race has subraces.

    :param str race: Race to determine if it has subraces.

    """
    try:
        subraces = [s for s in get_subraces_by_race(ALLOWED_PC_SUBRACES, race)][0]
    except IndexError:
        return False
    else:
        return subraces
