from dataclasses import dataclass
import logging

from notifications import prompt
from guides import GuidelineReader

log = logging.getLogger("thespian.tweaks")


class _GuidelineBuilder:
    """Class to build creation guideline characteristics.

    ===================================
    = SEPARATION CHARACTER DESCRIPTIONS
    ===================================

    SEMICOLON: Used to separate flags. i.e: ability=Strength;proficiency=skills
        Two flag options are designated in the above example: 'ability', and 'proficiency'.

    EQUAL SIGN: Used to separate option parameters. i.e ability=Strength,1
        The example above means Strength is a designated parameter for the ability flag.
        In this case the character would get an enhancement to Strength.
        There is more to this and is explained further below.

    COMMA: Used to set a parameter's number of applications. i.e: languages,2
        The example above means that a player can choose two languages.

    DOUBLE AMPERSAND: Used to seperate parameter options. i.e ability=Strength&&Dexterity,1
        The example above means the player can gain an enhancement in both Strength and Dexterity.

    DOUBLE PIPEBAR: Used to separater parameter options. i.e ability=Strength||Dexerity,1
        The example above means the player can choose a one time ehancement to Strength or Dexterity.

    """

    SEPARATOR_CHARS = (";", "=", ",", "&&", "||")

    @classmethod
    def build(cls, build_name: str, guideline_string: str) -> dict:
        """Translates 'guideline' strings into instructions."""
        if guideline_string is None:
            return dict()

        # Init
        super(_GuidelineBuilder, cls).__init__(guideline_string)

        guidelines = dict()

        # Separate flag string into raw pair strings. CHAR: ";"
        guideline_pairs = guideline_string.split(cls.SEPARATOR_CHARS[0])

        separator_ampersand = cls.SEPARATOR_CHARS[3]
        separator_comma = cls.SEPARATOR_CHARS[2]
        separator_equalsign = cls.SEPARATOR_CHARS[1]
        separator_pipes = cls.SEPARATOR_CHARS[4]

        # Cycle through raw string pairs.
        for guideline_pair in guideline_pairs:
            # Checks if "pair" is formatted to be splitted. CHAR ","
            if separator_comma not in guideline_pair:
                raise ValueError("Pairs must be formatted in 'name,value' pairs.")

            # Split pair into flag_name/flag_increment.
            guide_name, guide_increment = guideline_pair.split(separator_comma)

            # Check if flag_name has no equal sign character. CHAR "="
            if separator_equalsign not in guide_name:
                guidelines[guide_name] = {"increment": int(guide_increment)}
            else:
                guide_options = guide_name.split(separator_equalsign)
                guide_name = guide_options[0]

                # If double ampersand, save options as tuple
                # If double pipes, save options as list
                # If neither, encase option in list
                if separator_ampersand in guide_options[1]:
                    guide_options = tuple(guide_options[1].split(separator_ampersand))
                elif separator_pipes in guide_options[1]:
                    guide_options = guide_options[1].split(separator_pipes)
                else:
                    guide_options = [guide_options[1]]

                guidelines[guide_name] = {
                    "increment": int(guide_increment),
                    "options": guide_options,
                }

        return {build_name: guidelines}


class FeatGuidelineParser(_GuidelineBuilder):
    """Class to parse feat guidelines."""

    def __init__(self, feat, my_character):
        self.feat = feat
        super(_GuidelineBuilder, self).__init__()
        self.my_character = my_character
        self.guidelines = GuidelineReader.get_entry_guide_string("feats", self.feat)
        self.perks = GuidelineReader.get_feat_perks(self.feat)

    def _get_proficiency_options(self, prof_type: str) -> list:
        """Returns a list of bonus proficiencies for a feat by proficiency type."""
        return GuidelineReader.get_feat_proficiencies(self.feat, prof_type)

    def parse(self) -> dict:
        """Honors the specified flags for a feat."""
        parsed_guidelines = self.build("feats", self.guidelines)["feats"]
        if len(parsed_guidelines) == 0:
            return

        feat_guidelines = dict()

        for guide_name, guide_options in parsed_guidelines.items():
            guideline_increment = guide_options["increment"]
            if guideline_increment < 0:
                raise ValueError("Guideline 'increment' requires a positive value.")

            guideline_options = guide_options["options"]
            if len(guideline_options) < 1:
                raise ValueError("Guideline 'options' cannot be undefined.")

            if guide_name == "scores":
                if len(guideline_options) == 1:
                    my_ability = guideline_options[0]
                else:
                    # If 'savingthrows' guideline specified
                    # Add proficiency for ability saving throw.
                    if "savingthrows" not in parsed_guidelines:
                        my_ability = prompt(
                            "Choose an ability score to upgrade.",
                            guideline_options,
                        )
                    else:
                        my_ability = prompt(
                            "Choose an ability score to upgrade.",
                            guideline_options,
                            self.my_character["savingthrows"],
                        )
                        feat_guidelines["savingthrows"].append(my_ability)
                feat_guidelines[guide_name] = {my_ability: guideline_increment}

            if guide_name == "proficiency":
                # Get the type of proficiency bonus to apply.
                proficiency_type = guideline_options[0]

                # Get a list of the applicable proficiency selection options.
                guideline_options = self._get_proficiency_options(proficiency_type)

                # Tuple options will be appended as is as a list.
                if isinstance(guideline_options, tuple) and guideline_increment == 0:
                    feat_guidelines[guide_name] = list(guideline_options)

                # List/dict options allow the user to choose what to append.
                if isinstance(guideline_options, list) and guideline_increment > 0:
                    for increment_count in range(guideline_increment):
                        my_bonus = prompt(
                            f"Choose your bonus: '{guide_name} >> {proficiency_type}' ({increment_count + 1}):",
                            guideline_options,
                            self.my_character[proficiency_type],
                        )
                elif isinstance(guideline_options, dict) and guideline_increment > 0:
                    # Get the available proficiency groups.
                    selection_groups = tuple(guideline_options.keys())

                    # Create proficiency selection list from applicable groups.
                    proficiency_selections = []
                    for group in selection_groups:
                        if group not in self.my_character[proficiency_type]:
                            proficiency_selections += guideline_options[group]

                    # Replace guideline options with proficiency selections.
                    # Sort proficiency selections.
                    guideline_options = proficiency_selections
                    guideline_options.sort()

                    feat_guidelines[proficiency_type] = []
                    for increment_count in range(guideline_increment):
                        my_bonus = prompt(
                            f"Choose your bonus: '{guide_name} >> {proficiency_type}' ({increment_count + 1}):",
                            guideline_options,
                            self.my_character[proficiency_type],
                        )
                        guideline_options.remove(my_bonus)
                        feat_guidelines[proficiency_type].append(my_bonus)

            elif guide_name == "speed":
                speed_value = self.perks[guide_name]
                if speed_value != 0:
                    feat_guidelines[guide_name] = speed_value

            elif guide_name == "spells":
                bonus_spells = self.perks[guide_name]
                for index, spell in enumerate(bonus_spells):
                    if isinstance(spell, list):
                        spell_choice = prompt("Choose your bonus spell.", spell)
                        bonus_spells[index] = spell_choice

                feat_guidelines[guide_name] = bonus_spells

        return feat_guidelines


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
                self._set_ability_score(ability, bonus)
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

    def run_tweaks(self) -> None:
        """Executes ability score improvements upon the specified character data."""
        if self.character["level"] < 4:
            return

        num_of_upgrades = self._get_number_of_upgrades()

        while num_of_upgrades > 0:
            my_path = prompt(
                "Follow which upgrade path?", ["Upgrade Ability", "Choose Feat"]
            )

            # Path #1: Upgrade an Ability.
            if my_path == "Upgrade Ability":
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
                        self._set_ability_score(my_ability, my_bonus)
                elif my_bonus == 2:
                    my_ability = prompt(
                        "Which ability?",
                        ability_options,
                    )
                    self._set_ability_score(my_ability, my_bonus)

            # Path #2: Add a new Feat.
            elif my_path == "Choose Feat":
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
                    log.warn(
                        f"You don't meet the requirements for '{my_feat}'.",
                    )
                    my_feat = prompt(
                        f"Which feat do you want to acquire?",
                        feat_options,
                    )
                else:
                    self._add_feat_perks(my_feat)
                    self.character["feats"].append(my_feat)

            num_of_upgrades -= 1

    def _set_ability_score(self, ability: str, bonus: int = 1) -> None:
        """Applies a bonus to the ability (if applicable)."""
        if not self._is_adjustable(ability, bonus):
            log.warn(f"Ability '{ability}' is not adjustable with a bonus of {bonus}.")
            return

        new_score = self.character["scores"][ability] + bonus
        self.character["scores"][ability] = new_score


if __name__ == "__main__":
    x = FeatGuidelineParser(
        "Weapon Master",
        {
            "languages": ["Common"],
            "savingthrows": ["Constitution", "Strength"],
            "weapons": [],
        },
    )
    x.parse()
