from collections import OrderedDict
import logging
from math import floor
from random import choice, randint
import re

log = logging.getLogger("thespian.attributes")


class AttributeGenerator:
    """Class to handle the generation of character's attributes."""

    def __init__(self, primary_attributes: tuple | list, racial_bonus: dict):
        self.primary_attributes = primary_attributes
        self.racial_bonus = racial_bonus

    def generate(self) -> OrderedDict:
        """Generates/assigns character attributes."""
        attribute_set = OrderedDict()
        attribute_set["Strength"] = None
        attribute_set["Dexterity"] = None
        attribute_set["Constitution"] = None
        attribute_set["Intelligence"] = None
        attribute_set["Wisdom"] = None
        attribute_set["Charisma"] = None

        attribute_options = list(self.attribute_set.keys())
        result_set = self._roll_attribute_set()

        for _, attribute in enumerate(self.primary_attributes):
            attribute_options.remove(attribute)
            attribute_value = max(result_set)
            result_set.remove(attribute_value)
            attribute_set[attribute] = attribute_value

        for _ in range(0, 4):
            attribute = choice(attribute_options)
            attribute_options.remove(attribute)
            attribute_value = choice(result_set)
            result_set.remove(attribute_value)
            attribute_set[attribute] = attribute_value

        for attribute, bonus in self.racial_bonus.items():
            attribute_value = attribute_set[attribute] + bonus
            attribute_set[attribute] = attribute_value

        return attribute_set

    def _roll_attribute_set(self) -> list:
        """Generates six ability scores."""

        def generate_score():
            rolls = roll_die("4d6")
            rolls.remove(min(rolls))
            return sum(rolls)

        results = list()
        while sum(results) < 65 or min(results) < 8 or max(results) < 15:
            results = [generate_score() for _ in range(6)]

        return results


def generate_hit_points(
    level: int, hit_die: str, attributes: OrderedDict, roll_hp: bool
) -> tuple:
    """Generates the character's hit points."""
    if roll_hp:
        log.warning("Hit points will be randomly generated every level after the first.")
    else:
        log.warning("Hit points will be assigned a fixed number every level.")

    hit_die = int(hit_die)
    hit_die_string = f"{level}d{hit_die}"
    modifier = get_ability_modifier("Constitution", attributes)
    total_hit_points = hit_die + modifier

    if level > 1:
        die_rolls = list()
        for _ in range(1, level):
            if not roll_hp:
                hp_result = int((hit_die / 2) + 1)
            else:
                hp_result = randint(1, hit_die)
            hp_result = hp_result + modifier

            if hp_result < 1:
                hp_result = 1
            die_rolls.append(hp_result)
        total_hit_points += sum(die_rolls)

    return hit_die_string, total_hit_points


def get_ability_modifier(ability: str, scores: dict) -> int:
    """Returns modifier for ability in scores."""
    try:
        return floor((int(scores[ability]) - 10) / 2)
    except KeyError:
        return 0


def roll_die(format: str) -> list:
    """Rolls a die (i.e 4d6)."""
    if not isinstance(format, str):
        raise TypeError(f"Argument must be of type 'str'.")

    if not re.search("[0-9]d[0-9]", format):
        raise ValueError("Invalid die format used (i.e: 4d6).")

    num_of_rolls, die_type = format.split("d")
    num_of_rolls = int(num_of_rolls)
    die_type = int(die_type)

    if num_of_rolls < 1:
        raise ValueError("Must make at least 1 roll.")

    if die_type not in (1, 4, 6, 8, 10, 12, 20, 100):
        raise ValueError("Die type invalid.")

    return [randint(1, die_type) for r in range(num_of_rolls)]
