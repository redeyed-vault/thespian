from collections import OrderedDict
import random

from yari.dice import roll
from yari.exceptions import InheritanceError
from yari.loader import _read


class _Attributes:
    """DO NOT call class directly. Used to generate attribute features.
        Inherited by the following classes:

        - Charisma
        - Constitution
        - Dexterity
        - Intelligence
        - Strength
        - Wisdom

    """

    def __init__(self, score: int, skills: list) -> None:
        """
        Args:
            score (int): Character's chosen level.
            skills (list): Character's chosen skills.

        """
        self.attribute = self.__class__.__name__
        if self.attribute == "_Attributes":
            raise InheritanceError("this class must be inherited")

        self.attr = dict()
        self.attr["value"] = score
        self.attr["modifier"] = get_ability_modifier(self.attr.get("value"))
        self.attr["ability_checks"] = self.attr.get("modifier")
        self.attr["name"] = self.attribute
        self.attr["saving_throws"] = self.attr.get("modifier")
        self.attr["skills"] = dict()

        attribute_skills = list(x for x in self._get_skills_by_attribute())
        for skill in skills:
            if skill in attribute_skills:
                self.attr["skills"].update({skill: get_ability_modifier(score)})

    def _get_skills_by_attribute(self):
        """Returns a skill list by attribute."""
        for skill in _read(file="skills"):
            attribute = _read(skill, "ability", file="skills")
            if attribute == self.attribute:
                yield skill


class Charisma(_Attributes):
    def __init__(self, score: int, skills: list) -> None:
        super(Charisma, self).__init__(score, skills)


class Constitution(_Attributes):
    def __init__(self, score: int, skills: list) -> None:
        super(Constitution, self).__init__(score, skills)


class Dexterity(_Attributes):
    def __init__(self, score: int, skills: list) -> None:
        super(Dexterity, self).__init__(score, skills)


class Intelligence(_Attributes):
    def __init__(self, score: int, skills: list) -> None:
        super(Intelligence, self).__init__(score, skills)


class Strength(_Attributes):
    def __init__(self, score: int, skills: list) -> None:
        super(Strength, self).__init__(score, skills)
        self.attr["carry_capacity"] = score * 15
        self.attr["push_pull_carry"] = self.attr.get("carry_capacity") * 2
        self.attr["maximum_lift"] = self.attr.get("push_pull_carry")


class Wisdom(_Attributes):
    def __init__(self, score: int, skills: list) -> None:
        super(Wisdom, self).__init__(score, skills)


class AttributeGenerator:
    """Assigns abilities and their respective value/modifier pairs.
        Uses class' primary abilities in assignments.
        Applies racial bonuses to generated scores (if applicable)."""

    def __init__(self, primary_ability: dict, racial_bonus: dict, threshold=65) -> None:
        """
        Args:
            primary_ability (dict): Character class' primary abilities.
            racial_bonus (dict): Character racial bonuses.
            threshold (int): Ability score array minimal threshold total.

        """
        self.primary_ability = list(primary_ability.values())
        self.racial_bonus = racial_bonus
        self.threshold = threshold

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

        generated_scores = self._determine_ability_scores()
        # Assign highest values to class specific abilities first.
        for ability in self.primary_ability:
            value = max(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)

        # Assign remaining abilities/scores.
        for _ in range(0, 4):
            ability = random.choice(ability_choices)
            value = random.choice(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)

        self.score_array = score_array

        # Apply racial bonuses.
        for ability, bonus in self.racial_bonus.items():
            value = self.score_array.get(ability) + bonus
            self.score_array[ability] = value

    def _determine_ability_scores(self) -> list:
        """Generates six ability scores for assignment."""

        def _roll() -> int:
            rolls = list(roll("4d6"))
            rolls.remove(min(rolls))
            return sum(rolls)

        results = list()
        while sum(results) < self.threshold or min(results) < 8 or max(results) < 15:
            results = [_roll() for _ in range(6)]

        return results


def get_ability_modifier(score: int) -> int:
    """Returns ability modifier by score.

    Args:
        score (int): Score to retrieve modifier for.

    """
    return score is not 0 and int((score - 10) / 2) or 0
