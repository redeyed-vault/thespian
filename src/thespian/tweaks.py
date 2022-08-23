from dataclasses import dataclass
import logging

from notifications import prompt
from parsers import FeatGuidelineParser
from guides import GuidelineReader

log = logging.getLogger("thespian.tweaks")


@dataclass
class AbilityScoreImprovement:
    """Class to handle ability/feat upgrades."""

    character: dict

    def _add_feat_perks(self, feat: str) -> None:
        """Applies feat related perks."""
        parsed_attributes = FeatGuidelineParser(feat, self.character).parse()
        if parsed_attributes is None:
            return

        for flag, options in parsed_attributes.items():
            if flag == "ability":
                ability, bonus = options
                self._set_attribute(ability, bonus)
            else:
                self.character[flag] += options

    def _get_number_of_upgrades(self) -> int:
        """Returns the number of available upgrades."""
        level = self.character["level"]
        number_of_upgrades = 0
        for _ in range(1, level + 1):
            if (_ % 4) == 0 and _ != 20:
                number_of_upgrades += 1

        klass = self.character["klass"]
        if klass == "Fighter" and level >= 6:
            number_of_upgrades += 1
        if klass == "Rogue" and level >= 8:
            number_of_upgrades += 1
        if klass == "Fighter" and level >= 14:
            number_of_upgrades += 1
        if level >= 19:
            number_of_upgrades += 1

        return number_of_upgrades

    def _has_requirements(self, feat: str) -> bool:
        """Checks if feat requirements have been met."""
        klass = self.character["klass"]
        armors = self.character["armors"]

        # Character already has feat
        if feat in self.character["feats"]:
            return False

        # If Heavily, Lightly, or Moderately Armored feat or a Monk.
        # "Armor Related" or Weapon Master feat but already proficient.
        if (
            feat
            in (
                "Heavily Armored",
                "Lightly Armored",
                "Moderately Armored",
            )
            and klass == "Monk"
        ):
            return False

        elif feat in (
            "Heavily Armored",
            "Lightly Armored",
            "Moderately Armored",
            "Weapon Master",
        ):
            # Heavily Armored: Character already has heavy armor proficiency.
            # Lightly Armored: Character already has light armor proficiency.
            # Moderately Armored: Character already has medium armor proficiency.
            # Weapon Master: Character already has martial weapon proficiency.
            if feat == "Heavily Armored" and "Heavy" in armors:
                return False
            elif feat == "Lightly Armored" and "Light" in armors:
                return False
            elif feat == "Moderately Armored" and "Medium" in armors:
                return False
            elif feat == "Weapon Master" and "Martial" in self.character["weapons"]:
                return False

        # Cycle through ALL prerequisites for the feat.
        feat_prerequisites = GuidelineReader.get_feat_requirements(feat)
        for requirement, _ in feat_prerequisites.items():
            # Ignore requirements that are None
            if feat_prerequisites[requirement] is None:
                continue

            # Check ability requirements
            if requirement == "ability":
                for ability, minimum_score in feat_prerequisites[requirement].items():
                    my_score = self.character["scores"][ability]
                    if my_score < minimum_score:
                        return False

            # Check caster requirements
            if requirement == "caster":
                # If no spellcasting ability.
                if (
                    feat_prerequisites[requirement]
                    and self.character["spell_slots"] == "0"
                ):
                    return False

                # Magic Initiative requirements check.
                if feat == "Magic Initiative" and klass not in (
                    "Bard",
                    "Cleric",
                    "Druid",
                    "Sorcerer",
                    "Warlock",
                    "Wizard",
                ):
                    return False

                # Ritual Caster requirements check
                if feat == "Ritual Caster":
                    primary_ability = self.ability[0]
                    if primary_ability not in ("Intelligence", "Wisdom"):
                        return False

                    my_score = self.scores[primary_ability]
                    minimum_score = feat_prerequisites["ability"][primary_ability]

                    if my_score < minimum_score:
                        return False

            # Check proficiency requirements
            if requirement == "proficiency":
                if feat in (
                    "Heavy Armor Master",
                    "Heavily Armored",
                    "Medium Armor Master",
                    "Moderately Armored",
                ):
                    required_armors = feat_prerequisites[requirement]["armors"]
                    for armor in required_armors:
                        if armor not in required_armors:
                            return False

            # Check race requirements
            if requirement == "race":
                if self.character["race"] not in feat_prerequisites[requirement]:
                    return False

            # Check subrace requirements
            if requirement == "subrace":
                if self.character["subrace"] not in feat_prerequisites[requirement]:
                    return False

        return True

    def _is_adjustable(self, ability: str, bonus: int = 1) -> bool:
        """Checks if an ability is adjustable with the specified bonus (<= 20)."""
        if not isinstance(ability, str):
            raise TypeError("Argument 'ability' must be of type 'str'.")
        if not isinstance(bonus, int):
            raise TypeError("Argument 'bonus' must be of type 'int'.")

        attributes = self.character["scores"]
        if ability not in attributes:
            raise ValueError(f"Invalid ability '{ability}' specified.")
        if (attributes[ability] + bonus) > 20:
            return False

        return True

    def run_tweaks(self) -> None | bool:
        """Executes ability score improvements upon the specified character data."""
        if self.character["level"] < 4:
            logging.warning("Character level less than 4. No upgrades available.")
            return False

        upgrades_available = self._get_number_of_upgrades()

        while upgrades_available > 0:
            my_upgrade = prompt("Choose your upgrade:", ["Ability", "Feat"])

            # Path #1: Upgrade an Ability.
            if my_upgrade == "Ability":
                my_bonus = prompt("Apply how many points?", ["1", "2"])
                my_bonus = int(my_bonus)

                ability_options = [
                    a
                    for a in tuple(self.character["scores"].keys())
                    if self._is_adjustable(a, my_bonus)
                ]

                # Apply +2 bonus to one ability.
                # Apply +1 bonus to two abilities.
                if my_bonus == 1:
                    for _ in range(2):
                        my_ability = prompt(
                            "Which ability?",
                            ability_options,
                        )
                        ability_options.remove(my_ability)
                        self._set_attribute(my_ability, my_bonus)
                elif my_bonus == 2:
                    my_ability = prompt(
                        "Which ability?",
                        ability_options,
                    )
                    self._set_attribute(my_ability, my_bonus)

            # Path #2: Add a new Feat.
            elif my_upgrade == "Feat":
                feat_options = [
                    x
                    for x in GuidelineReader.get_all_feats()
                    if x not in self.character["feats"]
                ]

                my_feat = prompt(
                    "Which feat do you want to acquire?",
                    feat_options,
                )

                while not self._has_requirements(my_feat):
                    feat_options.remove(my_feat)
                    log.warning(
                        f"You don't meet the requirements for '{my_feat}'.",
                    )
                    my_feat = prompt(
                        f"Which feat do you want to acquire?",
                        feat_options,
                    )
                else:
                    self._add_feat_perks(my_feat)
                    self.character["feats"].append(my_feat)

            # Deincrement upgrade count.
            upgrades_available -= 1

    def _set_attribute(self, attribute: str, bonus: int = 1) -> None | bool:
        """Applies a bonus to the ability (if applicable)."""
        if not self._is_adjustable(attribute, bonus):
            log.warning(f"Attribute '{attribute}' is not adjustable.")
            return False

        new_score = self.character["scores"][attribute] + bonus
        self.character["scores"][attribute] = new_score


if __name__ == "__main__":
    x = FeatGuidelineParser(
        "Tavern Brawler",
        {
            "languages": ["Common"],
            "savingthrows": ["Constitution", "Strength"],
            "scores": {"Strength": 13, "Charisma": 18},
            "weapons": [],
        },
    )
    x.set(x.parse())
