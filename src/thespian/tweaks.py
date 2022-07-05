from dataclasses import dataclass
import logging

from notifications import prompt
from config import GuidelineSettings

log = logging.getLogger("thespian.tweaks")


class FeatOptionParser:
    """Generates and parses feat characteristic flags by feat.

    FLAG OPTION PARSER SYSTEM

    PIPEBAR: Used to separate flags. i.e: ability=Strength|proficiency=skills
        Two flag options are designated in the above example: 'ability', and 'proficiency'.

        ALLOWED FLAG OPTIONS:

        Designates certain instructions for applying feat related "perks" to a character.

            - ability
            - proficiency
            - saves
            - speed

    COMMA: Used to identify the number of occurences of a flag. i.e: languages,2
        The example above means that a player can choose two languages.

    EQUAL SIGN: Used to separate option parameters. i.e ability=Strength,0
        The example above means Strength is a designated parameter for the ability option.
        In this case the character would get an enhancement to Strength.
        There is more to this and is explained further below.

    DOUBLE AMPERSAND: Used to separater parameter options. i.e ability=Strength&&Dexerity,1
        The example above means the player can choose a one time ehancement to Strength or Dexterity.

    PLUS SIGN: Used to seperate parameter options. i.e ability=Strength+Dexterity
        The example above means the player can gain an enhancement in both Strength and Dexterity.

    """

    # Parser Option Separators
    PARSER_OPTIONS = "|"
    OPTION_INCREMENT = ","
    OPTION_PARAMETER = "="
    PARAM_SINGLE_SELECTION = "&&"
    PARAM_MULTIPLE_SELECTION = "+"

    def __init__(self, feat, prof):
        self.feat = feat
        self.profile = prof
        self.perks = get_feat_perks(self.feat)

    def _get_proficiency_options(self, prof_type: str) -> list:
        """Returns a list of bonus proficiencies for a feat by proficiency type."""
        return get_feat_proficiencies(self.feat, prof_type)

    def _get_sub_menu_options(self, available_options) -> dict | bool:
        """Creates a dictionary of sub menu options, if applicable."""
        if self.is_sub_menu(available_options):
            sub_options = dict()
            for option in available_options:
                sub_options[option] = self._get_proficiency_options(option)
            return sub_options
        return False

    @staticmethod
    def _is_sub_menu(available_options) -> bool:
        """Returns True if sub menu options are available. False otherwise."""
        for option in available_options:
            if not option.islower():
                return False
        return True

    def _parse_flags(self) -> dict:
        """Generates the characteristics for the specified feat."""
        parsed_flags = dict()
        raw_flags = self.perks.get("flags")
        if raw_flags is None:
            return parsed_flags

        flag_pairs = raw_flags.split(self.PARSER_OPTIONS)
        for flag_pair in flag_pairs:
            if self.OPTION_INCREMENT not in flag_pair:
                raise ValueError("Pairs must be formatted in 'name,value' pairs.")

            attribute_name, increment = flag_pair.split(self.OPTION_INCREMENT)
            if self.OPTION_PARAMETER not in attribute_name:
                parsed_flags[attribute_name] = {"increment": increment}
            else:
                flag_options = attribute_name.split(self.OPTION_PARAMETER)
                # Allowable flags: ability, proficiency, saves, speed
                attribute_name = flag_options[0]
                try:
                    if attribute_name not in (
                        "ability",
                        "proficiency",
                        "saves",
                        "speed",
                    ):
                        raise ValueError(
                            f"Illegal flag name '{attribute_name}' specified."
                        )
                except ValueError:
                    # pass
                    return parsed_flags
                if self.PARAM_SINGLE_SELECTION in flag_options[1]:
                    options = flag_options[1].split(self.PARAM_SINGLE_SELECTION)
                else:
                    options = flag_options[1]

                parsed_flags[attribute_name] = {
                    "increment": increment,
                    "options": options,
                }

        return parsed_flags

    def run(self) -> dict:
        """Honors the specified flags for a feat."""
        parsed_flag_list = self._parse_flags()
        if len(parsed_flag_list) == 0:
            return

        feat_flags = dict()
        for flag, options in parsed_flag_list.items():

            if flag in ("ability", "proficiency"):
                flag_increment_count = int(options["increment"])
                flag_menu_options = options["options"]
                if len(flag_menu_options) < 1:
                    raise ValueError("Malformed parser instructions error.")

            if flag == "ability":
                if flag_increment_count == 0:
                    raise ValueError(
                        "Flag attribute 'ability' requires a positive integer value."
                    )

                # For feats that use the 'saves' flag.
                # Limits choices based on current saving throw proficiencies.
                if "saves" in parsed_flag_list:
                    flag_menu_options = [
                        x for x in flag_menu_options if x not in self.profile["saves"]
                    ]

                if isinstance(flag_menu_options, str):
                    my_ability = flag_menu_options
                elif isinstance(flag_menu_options, list):
                    for _ in range(flag_increment_count):
                        my_ability = prompt(
                            "Choose the ability you would like to apply a bonus to.",
                            flag_menu_options,
                        )
                        flag_menu_options.remove(my_ability)
                        log.info(f"You selected the ability '{my_ability}'.")

                        # If 'saves' flag specified, add proficiency for ability saving throw.
                        if "saves" in parsed_flag_list:
                            self.profile["saves"].append(my_ability)
                            log.info(
                                f"You gained proficiency in the '{my_ability}' saving throw."
                            )

                bonus_value = self.perks[flag][my_ability]
                feat_flags[flag] = (my_ability, bonus_value)

            elif flag == "proficiency":
                # Increment value of 0 means append ALL listed bonuses.
                # Increment values other than 0 means add # of bonuses == increment value.
                chosen_options = dict()
                submenu_options = None

                if isinstance(flag_menu_options, str) and flag_increment_count == 0:
                    chosen_options[flag_menu_options] = self._get_proficiency_options(
                        flag_menu_options
                    )
                elif isinstance(flag_menu_options, list):
                    for _ in range(flag_increment_count):
                        my_bonus = prompt(
                            f"Choose your bonus: '{flag}'.", flag_menu_options
                        )
                        if not self._is_sub_menu(flag_menu_options):
                            flag_menu_options.remove(my_bonus)
                        else:
                            # Generate submenu options, if applicable.
                            if submenu_options is None:
                                submenu_options = self._get_sub_menu_options(
                                    flag_menu_options
                                )
                                submenu_options[my_bonus] = [
                                    x
                                    for x in submenu_options[my_bonus]
                                    if x not in self.profile[my_bonus]
                                ]

                            # Create storage handler for selections, if applicable.
                            if len(chosen_options) == 0:
                                for opt in submenu_options:
                                    chosen_options[opt] = list()

                            submenu_choice = prompt(
                                f"Choose submenu option: '{my_bonus}'.",
                                submenu_options.get(my_bonus),
                            )
                            chosen_options[my_bonus].append(submenu_choice)
                            submenu_options[my_bonus].remove(submenu_choice)
                            # Reset the submenu options after use
                            submenu_options = None
                            log.info(
                                f"You selected the {flag} ({my_bonus}) bonus '{submenu_choice}'."
                            )

                elif isinstance(flag_menu_options, str):
                    for prof_type in flag_menu_options.split(
                        self.PARAM_MULTIPLE_SELECTION
                    ):
                        chosen_proficiencies = list()

                        # Pull full collection of bonus proficiencies,
                        proficiency_options = get_feat_proficiencies(
                            self.feat, prof_type
                        )
                        # If collection is dict, sort through sub categories,
                        # And choose only the unselected options in that category.
                        # Otherwise, simply sort out the unselected options
                        if isinstance(proficiency_options, dict):
                            temp = list()
                            for types in tuple(proficiency_options.keys()):
                                if types not in self.profile[prof_type]:
                                    temp += proficiency_options[types]

                            proficiency_options = temp
                        else:
                            proficiency_options = [
                                x
                                for x in proficiency_options
                                if x not in self.profile[prof_type]
                            ]

                        for _ in range(flag_increment_count):
                            # Clear out the temporarily chosen options.
                            proficiency_options = [
                                x
                                for x in proficiency_options
                                if x not in chosen_proficiencies
                            ]
                            my_bonus = prompt(
                                f"Choose your bonus: {flag}.", proficiency_options
                            )
                            chosen_proficiencies.append(my_bonus)
                            proficiency_options.remove(my_bonus)
                            log.info(
                                f"You selected the {flag} ({prof_type}) bonus '{my_bonus}'."
                            )

                        chosen_options[prof_type] = chosen_proficiencies

                for k, v in chosen_options.items():
                    feat_flags[k] = v

            elif flag == "speed":
                speed_value = self.perks[flag]
                if speed_value != 0:
                    feat_flags[flag] = speed_value

            elif flag == "spells":
                bonus_spells = self.perks[flag]
                for index, spell in enumerate(bonus_spells):
                    if isinstance(spell, list):
                        spell_choice = prompt("Choose your bonus spell.", spell)
                        bonus_spells[index] = spell_choice
                        log.info(f"You selected the spell {spell_choice}.")

                feat_flags[flag] = bonus_spells

        return feat_flags


@dataclass
class AbilityScoreImprovement:
    """Used to apply ability and/or feat upgrades."""

    character: dict

    def _add_feat_perks(self, feat: str) -> None:
        """Applies feat related perks."""
        parsed_attributes = FeatOptionParser(feat, self.character).run()
        if parsed_attributes is None:
            return

        for flag, options in parsed_attributes.items():
            if flag == "ability":
                ability, bonus = options
                self._set_ability_score(ability, bonus)
            else:
                self.character[flag] += options

    def _count_upgrades(self) -> int:
        """Returns the number of available upgrades."""
        upgrade_count = 0
        for x in range(1, self.character["level"] + 1):
            if (x % 4) == 0 and x != 20:
                upgrade_count += 1
        if self.character["klass"] == "Fighter" and self.character["level"] >= 6:
            upgrade_count += 1
        if self.character["klass"] == "Rogue" and self.character["level"] >= 8:
            upgrade_count += 1
        if self.character["klass"] == "Fighter" and self.character["level"] >= 14:
            upgrade_count += 1
        if self.character["level"] >= 19:
            upgrade_count += 1

        return upgrade_count

    def _has_requirements(self, feat: str) -> bool:
        """Checks if feat requirements have been met."""

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
            and self.character["klass"] == "Monk"
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
            if feat == "Heavily Armored" and "Heavy" in self.character["armors"]:
                return False
            elif feat == "Lightly Armored" and "Light" in self.character["armors"]:
                return False
            elif feat == "Moderately Armored" and "Medium" in self.character["armors"]:
                return False
            elif feat == "Weapon Master" and "Martial" in self.character["weapons"]:
                return False

        # Cycle through ALL prerequisites for the feat.
        prerequisite = get_feat_requirements(feat)
        for requirement, _ in prerequisite.items():
            # Ignore requirements that are None
            if prerequisite.get(requirement) is None:
                continue

            # Check ability requirements
            if requirement == "ability":
                for ability, required_score in prerequisite.get(requirement).items():
                    my_score = self.character["scores"][ability]
                    if my_score < required_score:
                        return False

            # Check caster requirements
            if requirement == "caster":
                # If no spellcasting ability.
                if prerequisite[requirement] and self.character["spellslots"] == "0":
                    return False

                # Magic Initiative requirements check
                if feat == "Magic Initiative" and self.character["klass"] not in (
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
                    my_score = self.scores[primary_ability]
                    required_score = prerequisite["ability"][primary_ability]

                    if my_score < required_score:
                        return False

            # Check proficiency requirements
            if requirement == "proficiency":
                if feat in (
                    "Heavy Armor Master",
                    "Heavily Armored",
                    "Medium Armor Master",
                    "Moderately Armored",
                ):
                    armors = prerequisite.get(requirement).get("armors")
                    for armor in armors:
                        if armor not in self.character["armors"]:
                            return False

            # Check race requirements
            if requirement == "race":
                if self.character["race"] not in prerequisite.get(requirement):
                    return False

            # Check subrace requirements
            if requirement == "subrace":
                if self.character["subrace"] not in prerequisite.get(requirement):
                    return False

        return True

    def _is_adjustable(self, ability: str, bonus: int = 1) -> bool:
        """Checks if the specified ability is adjustable with the specified bonus (<= 20)."""
        if not isinstance(ability, str):
            raise TypeError("Argument 'ability' must be of type 'str'.")
        if not isinstance(bonus, int):
            raise TypeError("Argument 'bonus' must be of type 'int'.")
        if ability not in self.character["scores"]:
            raise ValueError(f"Invalid ability '{ability}' specified.")
        if (self.character["scores"][ability] + bonus) > 20:
            return False

        return True

    def run(self) -> None:
        """Executes ability score improvements upon the specified character data."""
        if self.character["level"] < 4:
            return

        num_of_upgrades = self._count_upgrades()
        while num_of_upgrades > 0:
            if num_of_upgrades > 1:
                log.info(f"You have {num_of_upgrades} upgrades available.")
            else:
                log.info("You have 1 upgrade available.")

            my_path = prompt(
                "Follow which upgrade path?", ["Upgrade Ability", "Choose Feat"]
            )

            # Path #1: Upgrade an Ability.
            if my_path == "Upgrade Ability":
                my_bonus = prompt("Apply how many points?", ["1", "2"])
                log.info(f"You chose an ability bonus of: +{my_bonus}.")
                my_bonus = int(my_bonus)

                ability_options = [
                    a
                    for a in (
                        "Strength",
                        "Dexterity",
                        "Constitution",
                        "Intelligence",
                        "Wisdom",
                        "Charisma",
                    )
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
                    x for x in get_feats_list() if x not in self.character["feats"]
                ]

                my_feat = prompt(
                    "Which feat do you want to acquire?",
                    feat_options,
                )
                log.info(f"Checking requirements for the requested feat {my_feat}...")

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
                    log.info(f"You selected the feat {my_feat}.")

            num_of_upgrades -= 1

    def _set_ability_score(self, ability: str, bonus: int = 1) -> None:
        """Applies a bonus to the specified ability (if applicable)."""
        if not self._is_adjustable(ability, bonus):
            log.warn(f"Ability '{ability}' is not adjustable with a bonus of {bonus}.")
        else:
            new_score = self.character.get("scores").get(ability) + bonus
            self.character["scores"][ability] = new_score
            log.info(f"You applied a +{bonus} bonus to your {ability}.")
            log.info(f"Your {ability} score is now {new_score}.")


def get_feat_perks(feat_name: str):
    """Returns perks by feat."""
    return GuidelineSettings.feats[feat_name]["perk"]


def get_feat_proficiencies(feat: str, prof_type: str):
    """Returns bonus proficiencies by feat and proficiency type."""
    return GuidelineSettings.feats[feat]["perk"][prof_type]


def get_feat_requirements(feat_name: str):
    """Returns requirements by feat."""
    return GuidelineSettings.feats[feat_name]["required"]


def get_feats_list() -> tuple:
    """Returns a tuple of all feats."""
    return tuple(GuidelineSettings.feats.keys())
