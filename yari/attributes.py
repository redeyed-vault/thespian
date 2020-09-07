from collections import OrderedDict
import random

from yari.dice import roll
from yari.loader import load


class AttributeGenerator:
    """
    Assigns abilities by class, and adds racial bonuses in value/modifier pairs.

    :param dict primary_ability: Character class' primary abilities.
    :param dict racial_bonus: Character racial bonuses.
    :param int threshold: Ability score array minimal threshold total.

    """

    def __init__(
        self, primary_ability: dict, racial_bonus: dict, threshold: int = 65
    ) -> None:
        self.primary_ability = primary_ability
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
        for ability in list(self.primary_ability.values()):
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


class _Attributes:
    """
    DO NOT call class directly. Used to generate ability attributes.

    Inherited by the following classes:

        - Charisma
        - Constitution
        - Dexterity
        - Intelligence
        - Strength
        - Wisdom

    :param int score: The value of the specified ability score.
    :param list skills: The character's skill list.

    """

    def __init__(self, score: int, skills: list) -> None:
        self.attribute = self.__class__.__name__
        if self.attribute == "_Attributes":
            raise Exception(
                "This class must be inherited to use. It is currently used by "
                "the Charisma, Constitution, Dexterity, Intelligence, Strength, "
                "and Wisdom 'attribute' classes."
            )

        self.score = score
        self.attr = dict()
        self.attr["value"] = score
        self.attr["modifier"] = get_ability_modifier(self.attr.get("value"))
        self.attr["ability_checks"] = self.attr.get("modifier")
        self.attr["name"] = self.attribute
        self.attr["saving_throws"] = self.attr.get("modifier")
        self.attr["skills"] = dict()

        attribute_skills = [x for x in self._get_skills_by_attribute()]
        for skill in skills:
            if skill in attribute_skills:
                self.attr["skills"].update({skill: get_ability_modifier(score)})

    def __repr__(self):
        return '<{} score="{}">'.format(self.attribute, self.score)

    def _get_skills_by_attribute(self):
        """Returns a skill list by attribute."""
        for skill in load(file="skills"):
            attribute = load(skill, "ability", file="skills")
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


def get_ability_modifier(score: int) -> int:
    """
    Returns ability modifier by score.

    :param int score: Score to calculate modifier for.

    """
    return score != 0 and int((score - 10) / 2) or 0
