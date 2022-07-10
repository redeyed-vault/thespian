from collections import OrderedDict
from dataclasses import dataclass
import logging
from math import floor
from random import choice, randint
import re

log = logging.getLogger("thespian.attributes")


@dataclass
class AttributeGenerator:
    """Class to generate character's base attributes."""

    primary_attributes: tuple | list
    racial_bonus: dict
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

        # Generate six ability scores.
        my_rolls = self._roll_ability_array(self.threshold)

        # Assign primary/secondary attributes first.
        for rank_index, attribute in enumerate(self.primary_attributes):
            attribute_value = max(my_rolls)
            my_attributes[attribute] = attribute_value

            attribute_options.remove(attribute)
            my_rolls.remove(attribute_value)

            ranking_text_labels = ("primary", "secondary")
            ranking_text = ranking_text_labels[rank_index]
            log.info(
                f"Your {ranking_text} class ability '{attribute}' score was set to {attribute_value}."
            )

        # Assign the remaining attributes.
        for _ in range(0, 4):
            attribute = choice(attribute_options)
            attribute_options.remove(attribute)

            attribute_value = choice(my_rolls)
            my_rolls.remove(attribute_value)

            my_attributes[attribute] = attribute_value
            log.info(f"Your '{attribute}' score was set to {attribute_value}.")

        # Apply racial bonuses.
        for attribute, bonus in self.racial_bonus.items():
            attribute_value = my_attributes[attribute] + bonus
            my_attributes[attribute] = attribute_value
            log.info(
                f"A bonus was applied to your '{attribute}' score {attribute_value} ({bonus})."
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
