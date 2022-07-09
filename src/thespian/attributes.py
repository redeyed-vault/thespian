from collections import OrderedDict
from dataclasses import dataclass
import logging
from math import floor
from random import choice, randint
import re

log = logging.getLogger("thespian.attributes")


@dataclass
class AttributeGenerator:
    """Generates values for the six basic attributes."""

    ability: tuple | list
    bonus: dict
    threshold: int = 65

    def generate(self) -> OrderedDict:
        """Generates and assigns character's ability scores."""
        my_attributes = OrderedDict()
        my_attributes["Strength"] = None
        my_attributes["Dexterity"] = None
        my_attributes["Constitution"] = None
        my_attributes["Intelligence"] = None
        my_attributes["Wisdom"] = None
        my_attributes["Charisma"] = None

        attribute_options = [
            "Strength",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
        ]

        # Generate six ability scores
        # Assign primary class abilities first
        # Assign the remaining abilities
        # Apply racial bonuses
        my_rolls = self._roll_ability_array(self.threshold)
        for adj_index, ability in enumerate(self.ability):
            value = max(my_rolls)
            my_attributes[ability] = value
            attribute_options.remove(ability)
            my_rolls.remove(value)
            adjective_text = ("primary", "secondary")
            log.info(
                f"Your {adjective_text[adj_index]} class ability '{ability}' score was set to {value}."
            )

        for _ in range(0, 4):
            ability = choice(attribute_options)
            value = choice(my_rolls)
            my_attributes[ability] = value
            attribute_options.remove(ability)
            my_rolls.remove(value)
            log.info(f"Your '{ability}' score was set to {value}.")

        for ability, bonus in self.bonus.items():
            value = my_attributes[ability] + bonus
            my_attributes[ability] = value
            log.info(
                f"A bonus was applied to your '{ability}' score {value} ({bonus})."
            )

        return my_attributes

    def _roll_ability_array(self, threshold: int = 65) -> list:
        """Generates six ability scores."""

        def generate_score():
            rolls = roll_die("4d6")
            rolls.remove(min(rolls))
            return sum(rolls)

        results = list()
        while sum(results) < threshold or min(results) < 8 or max(results) < 15:
            results = [generate_score() for _ in range(6)]

        return results


def generate_hit_points(
    level: int, hit_die: str, attributes: OrderedDict, roll_hp: bool
) -> tuple:
    """Generates the character's hit points."""
    if roll_hp:
        log.warn("Hit points will be randomly generated every level after the first.")
    else:
        log.warn("Hit points will be assigned a fixed number every level.")

    hit_die = int(hit_die)
    hit_die_string = f"{level}d{hit_die}"
    modifier = get_ability_modifier("Constitution", attributes)
    total_hit_points = hit_die + modifier
    log.info(f"level 1: you have {total_hit_points} ({modifier}) hit points.")
    if level > 1:
        die_rolls = list()
        for current_level in range(1, level):
            if not roll_hp:
                hp_result = int((hit_die / 2) + 1)
            else:
                hp_result = randint(1, hit_die)
            hp_result = hp_result + modifier
            if hp_result < 1:
                hp_result = 1
            die_rolls.append(hp_result)
            log.info(
                f"level {current_level + 1}: you gained {hp_result} ({modifier}) hit points."
            )
        total_hit_points += sum(die_rolls)
        log.info(f"You have {total_hit_points} hit points.")

    return hit_die_string, total_hit_points


def get_ability_modifier(ability: str, scores: dict) -> int:
    """Returns modifier for ability in scores."""
    try:
        return floor((int(scores[ability]) - 10) / 2)
    except KeyError:
        return 0


def roll_die(format: str):
    """Rolls a die (i.e 4d6)."""
    if not isinstance(format, str):
        raise TypeError(f"Argument must be of type 'str'.")

    if not re.search("[0-9]d[0-9]", format):
        raise ValueError("Invalid die format used (i.e: 4d6).")

    num_of_rolls, die_type = die_string = format.split("d")
    num_of_rolls = int(num_of_rolls)
    die_type = int(die_type)

    if num_of_rolls < 1:
        raise ValueError("Must make at least 1 roll.")

    if die_type not in (1, 4, 6, 8, 10, 12, 20, 100):
        raise ValueError("Die type invalid.")

    return [randint(1, die_type) for r in range(num_of_rolls)]
