from dataclasses import dataclass
import random
import re

from .errors import DieArgumentError
from .utils import _e


def roll(string: str):
    """
    Rolls die by die string format.

    :param str string: Die string format value i.e: 2d6, 10d8, etc.

    """
    if not isinstance(string, str):
        raise DieArgumentError("Argument 'string' must be of type 'str'.")

    if not re.search("[0-9]d[0-9]", string):
        raise DieArgumentError("Argument 'string' has an invalid format (i.e: 4d6).")

    string = string.split("d")
    num_of_rolls = int(string[0])
    die_type = int(string[1])

    if num_of_rolls < 1:
        raise DieArgumentError("Argument 'string' has an invalid 'num_of_rolls' value.")

    if die_type not in (1, 4, 6, 8, 10, 12, 20, 100):
        raise DieArgumentError("Argument 'string' has an invalid 'die_type' value.")

    for _ in range(num_of_rolls):
        yield random.randint(1, die_type)


@dataclass
class AttributeGenerator:
    """Generates values for the six basic attributes."""

    _ability: tuple
    _bonus: dict
    _threshold: int = 65

    def roll(self):
        """Rolls 4d6 six times to generate abilty scores."""

        def determine_ability_scores(threshold):
            def _roll():
                rolls = list(roll("4d6"))
                rolls.remove(min(rolls))
                return sum(rolls)

            results = list()
            while sum(results) < threshold or min(results) < 8 or max(results) < 15:
                results = [_roll() for _ in range(6)]

            return results

        from collections import OrderedDict

        score_array = OrderedDict()
        score_array["Strength"] = None
        score_array["Dexterity"] = None
        score_array["Constitution"] = None
        score_array["Intelligence"] = None
        score_array["Wisdom"] = None
        score_array["Charisma"] = None

        ability_choices = [
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
        generated_scores = determine_ability_scores(self._threshold)
        for ability in self._ability:
            value = max(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)
            _e(f"Ability '{ability}' set to >> {value}", "green")

        for _ in range(0, 4):
            from random import choice

            ability = choice(ability_choices)
            value = choice(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)
            _e(f"Ability '{ability}' set to >> {value}", "yellow")

        for ability, bonus in self._bonus.items():
            value = score_array.get(ability) + bonus
            score_array[ability] = value
            _e(f"Applied {bonus} bonus to '{ability}' ({value}).", "green")

        return score_array
