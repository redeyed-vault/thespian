from dataclasses import dataclass

from .errors import AbilityScoreImprovementError, FlagParserError
from .sources import Load
from .utils import _ok, _warn, get_character_feats, prompt


class FeatOptionParser:
    """Generates and parses feat characteristic flags by feat.

    FLAG OPTION PARSER SYSTEM

    PIPEBAR: Used to separate flags. i.e: ability=Strength|proficiency=skills
        Two flag options are designated in the above example: 'ability', and 'proficiency'.

        ALLOWED FLAG OPTIONS: Designates certain instructions for generating a character.
            - ability
            - proficiency
            - savingthrows
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
        self._feat = feat
        self._profile = prof
        self._perks = Load.get_columns(self._feat, "perk", source_file="feats")

    def _parse_flags(self):
        """Generates flag characteristics for the chosen feat."""
        parsed_flags = dict()
        raw_flags = self._perks.get("flags")
        if raw_flags == "none":
            return parsed_flags

        flag_pairs = raw_flags.split(self.PARSER_OPTIONS)
        for flag_pair in flag_pairs:
            if self.OPTION_INCREMENT not in flag_pair:
                raise FlagParserError(
                    "Pairs must be formatted in name,value pairs with a ',' separator."
                )

            attribute_name, increment = flag_pair.split(self.OPTION_INCREMENT)
            if self.OPTION_PARAMETER not in attribute_name:
                parsed_flags[attribute_name] = {"increment": increment}
            else:
                flag_options = attribute_name.split(self.OPTION_PARAMETER)
                # Allowable flags: ability, proficiency, savingthrows, speed
                attribute_name = flag_options[0]
                try:
                    if attribute_name not in (
                        "ability",
                        "proficiency",
                        "savingthrows",
                        "speed",
                    ):
                        raise FlagParserError(
                            f"Illegal flag name '{attribute_name}' specified."
                        )
                except FlagParserError:
                    pass
                if self.PARAM_SINGLE_SELECTION in flag_options[1]:
                    options = flag_options[1].split(self.PARAM_SINGLE_SELECTION)
                else:
                    options = flag_options[1]
                parsed_flags[attribute_name] = {
                    "increment": increment,
                    "options": options,
                }

        return parsed_flags

    def run(self):
        """Parses the generated flags for the chosen feat."""

        def is_sub_menu(available_options):
            for opt in available_options:
                if not opt.islower():
                    return False
            return True

        def get_proficiency_options(prof_type):
            return Load.get_columns(self._feat, "perk", prof_type, source_file="feats")

        def get_sub_menu_options(available_options):
            if is_sub_menu(available_options):
                sub_options = dict()
                for opt in available_options:
                    sub_options[opt] = get_proficiency_options(opt)
                return sub_options
            return False

        final_flag = self._parse_flags()
        if len(final_flag) == 0:
            return

        parsed_flag = dict()
        for flag, options in final_flag.items():

            if flag in ("ability", "proficiency"):
                increment = int(options["increment"])
                menu_options = options["options"]
                if len(menu_options) < 1:
                    raise FlagParserError("Malformed parser instructions error.")

            if flag == "ability":
                if increment == 0:
                    raise FlagParserError(
                        "Flag attribute 'ability' requires a positive integer value."
                    )

                # For feats that use the 'savingthrows' flag.
                # Limits choices based on current saving throw proficiencies.
                if "savingthrows" in final_flag:
                    menu_options = [
                        x
                        for x in menu_options
                        if x not in self._profile.get("savingthrows")
                    ]

                if isinstance(menu_options, str):
                    ability_choice = menu_options
                elif isinstance(menu_options, list):
                    for _ in range(increment):
                        ability_choice = prompt(
                            "Choose your bonus ability.", menu_options
                        )
                        menu_options.remove(ability_choice)
                        _ok(f"Added ability >> {ability_choice}")

                        # If 'savingthrows' flag specified, add proficiency for ability saving throw.
                        if "savingthrows" in final_flag:
                            self._profile["savingthrows"].append(ability_choice)
                            _ok(f"Added saving throw proficiency >> {ability_choice}")

                bonus_value = self._perks[flag][ability_choice]
                parsed_flag[flag] = (ability_choice, bonus_value)

            elif flag == "proficiency":
                # Increment value of 0 means add all listed bonuses.
                # Increment value other than 0 means add # of bonuses == increment value.
                chosen_options = dict()
                submenu_options = None

                if isinstance(menu_options, str) and increment == 0:
                    chosen_options[menu_options] = get_proficiency_options(menu_options)

                elif isinstance(menu_options, list):
                    for _ in range(increment):
                        menu_choice = prompt(
                            f"Choose your bonus: '{flag}'.", menu_options
                        )
                        if not is_sub_menu(menu_options):
                            menu_options.remove(menu_choice)
                        else:
                            # Generate submenu options, if applicable.
                            if submenu_options is None:
                                submenu_options = get_sub_menu_options(menu_options)
                                submenu_options[menu_choice] = [
                                    x
                                    for x in submenu_options[menu_choice]
                                    if x not in self._profile[menu_choice]
                                ]

                            # Create storage handler for selections, if applicable.
                            if len(chosen_options) == 0:
                                for opt in submenu_options:
                                    chosen_options[opt] = list()

                            submenu_choice = prompt(
                                f"Choose submenu option: '{menu_choice}'.",
                                submenu_options.get(menu_choice),
                            )
                            chosen_options[menu_choice].append(submenu_choice)
                            submenu_options[menu_choice].remove(submenu_choice)
                            # Reset the submenu options after use
                            submenu_options = None
                            _ok(f"Added {flag} ({menu_choice}) >> {submenu_choice}")

                elif isinstance(menu_options, str):
                    for prof_type in menu_options.split(self.PARAM_MULTIPLE_SELECTION):
                        chosen_proficiencies = list()

                        # Pull full collection of bonus proficiencies,
                        proficiency_options = Load.get_columns(
                            self._feat, "perk", prof_type, source_file="feats"
                        )
                        # If collection is dict, sort through sub categories,
                        # And choose only the unselected options in that category.
                        # Otherwise, simply sort out the unselected options
                        if isinstance(proficiency_options, dict):
                            temp = list()
                            for types in tuple(proficiency_options.keys()):
                                if types not in self._profile[prof_type]:
                                    temp += proficiency_options[types]

                            proficiency_options = temp
                        else:
                            proficiency_options = [
                                x
                                for x in proficiency_options
                                if x not in self._profile[prof_type]
                            ]

                        for _ in range(increment):
                            # Clear out the temporarily chosen options.
                            proficiency_options = [
                                x
                                for x in proficiency_options
                                if x not in chosen_proficiencies
                            ]
                            menu_choice = prompt(
                                f"Choose your bonus: {flag}.", proficiency_options
                            )
                            chosen_proficiencies.append(menu_choice)
                            proficiency_options.remove(menu_choice)
                            _ok(f"Added {flag} ({prof_type}) >> {menu_choice}")
                        chosen_options[prof_type] = chosen_proficiencies

                for k, v in chosen_options.items():
                    parsed_flag[k] = v

            elif flag == "speed":
                speed_value = self._perks[flag]
                if speed_value != 0:
                    parsed_flag[flag] = speed_value

            elif flag == "spells":
                bonus_spells = self._perks[flag]
                for index, spell in enumerate(bonus_spells):
                    if isinstance(spell, list):
                        spell_choice = prompt("Choose your bonus spell.", spell)
                        bonus_spells[index] = spell_choice
                        _ok(f"Added spell >> {spell_choice}")
                parsed_flag[flag] = bonus_spells

        return parsed_flag


@dataclass
class AbilityScoreImprovement:
    """Used to apply ability and/or feat upgrades."""

    _character: dict

    def _add_feat_perks(self, feat):
        """Applies feat related perks."""
        parsed_attributes = FeatOptionParser(feat, self._character).run()
        if parsed_attributes is None:
            return

        for flag, options in parsed_attributes.items():
            if flag == "ability":
                ability, bonus = options
                self._set_ability_score(ability, bonus)
            else:
                self._character[flag] += options

    def _has_requirements(self, feat):
        """Checks if feat requirements have been met."""

        def get_feat_requirements(feat_name: str, use_local: bool = True):
            return Load.get_columns(
                feat_name, "required", source_file="feats", use_local=use_local
            )

        # Character already has feat
        if feat in self._character["feats"]:
            return False

        # If Heavily, Lightly, or Moderately Armored feat and a Monk.
        # "Armor Related" or Weapon Master feat but already proficient.
        if (
            feat
            in (
                "Heavily Armored",
                "Lightly Armored",
                "Moderately Armored",
            )
            and self._character["klass"] == "Monk"
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
            if feat == "Heavily Armored" and "Heavy" in self._character["armors"]:
                return False
            elif feat == "Lightly Armored" and "Light" in self._character["armors"]:
                return False
            elif feat == "Moderately Armored" and "Medium" in self._character["armors"]:
                return False
            elif feat == "Weapon Master" and "Martial" in self._character["weapons"]:
                return False

        # Go through ALL prerequisites.
        prerequisite = get_feat_requirements(feat)
        for requirement, _ in prerequisite.items():
            # Ignore requirements that are None
            if prerequisite.get(requirement) is None:
                continue

            # Check ability requirements
            if requirement == "ability":
                for ability, required_score in prerequisite.get(requirement).items():
                    my_score = self._character["scores"][ability]
                    if my_score < required_score:
                        return False

            # Check caster requirements
            if requirement == "caster":
                # If caster prerequisite True
                if prerequisite.get(requirement):
                    # Check if character has spellcasting ability
                    if self._character["spellslots"] == "0":
                        return False

                    # Magic Initiative class check
                    if feat == "Magic Initiative" and self._character["klass"] not in (
                        "Bard",
                        "Cleric",
                        "Druid",
                        "Sorcerer",
                        "Warlock",
                        "Wizard",
                    ):
                        return False

                    """
                    # Ritual Caster class check
                    if feat == "Ritual Caster":
                        primary_ability = self.ability[0]
                        my_score = self.scores.get(primary_ability)
                        required_score = prerequisite.get("ability").get(primary_ability)

                        if my_score < required_score:
                            return False
                    """

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
                        if armor not in self._character["armors"]:
                            return False

            # Check race requirements
            if requirement == "race":
                if self._character["race"] not in prerequisite.get(requirement):
                    return False

            # Check subrace requirements
            if requirement == "subrace":
                if self._character["subrace"] not in prerequisite.get(requirement):
                    return False

        return True

    def _is_adjustable(self, ability, bonus=1):
        """Checks if ability is adjustable < 20."""
        if not isinstance(ability, str):
            raise AbilityScoreImprovementError(
                "Argument 'ability' must be of type 'str'."
            )

        if not isinstance(bonus, int):
            raise AbilityScoreImprovementError(
                "Argument 'bonus' must be of type 'int'."
            )

        if ability not in self._character["scores"]:
            raise AbilityScoreImprovementError(
                f"Invalid ability '{ability}' specified."
            )

        if (self._character["scores"][ability] + bonus) > 20:
            return False

        return True

    def run(self):
        """Executes the ability score improvement class."""
        from math import floor

        # TODO: Incorporate hp into character sheet.
        # Determine actual hp.
        modifier = floor((self._character["scores"]["Constitution"] - 10) / 2)
        self._character["hp"] += modifier * self._character["level"]

        if self._character["level"] < 4:
            return

        num_of_upgrades = 0
        for x in range(1, self._character["level"] + 1):
            if (x % 4) == 0 and x != 20:
                num_of_upgrades += 1
        if self._character["klass"] == "Fighter" and self._character["level"] >= 6:
            num_of_upgrades += 1
        if self._character["klass"] == "Rogue" and self._character["level"] >= 8:
            num_of_upgrades += 1
        if self._character["klass"] == "Fighter" and self._character["level"] >= 14:
            num_of_upgrades += 1
        if self._character["level"] >= 19:
            num_of_upgrades += 1

        while num_of_upgrades > 0:
            if num_of_upgrades > 1:
                _ok(f"You have {num_of_upgrades} upgrades available.")
            else:
                _ok("You have 1 upgrade available.")

            upgrade_path_options = ["Ability", "Feat"]
            upgrade_path = prompt(
                "Which path do you want to follow?", upgrade_path_options
            )

            # Path #1: Upgrade an Ability.
            # Path #2: Add a new Feat.
            if upgrade_path == "Ability":
                bonus_choice = prompt(
                    "Do you want an upgrade of a +1 or +2?", ["1", "2"]
                )
                ability_upgrade_options = (
                    "Strength",
                    "Dexterity",
                    "Constitution",
                    "Intelligence",
                    "Wisdom",
                    "Charisma",
                )
                bonus_choice = int(bonus_choice)
                ability_upgrade_options = [
                    x
                    for x in ability_upgrade_options
                    if self._is_adjustable(x, bonus_choice)
                ]
                # Apply +1 bonus to two abilities.
                # Apply +2 bonus to one ability.
                if bonus_choice == 1:
                    _ok("You may apply a +1 to two different abilities.")
                    for _ in range(2):
                        upgrade_choice = prompt(
                            "Which ability do you want to upgrade?",
                            ability_upgrade_options,
                        )
                        ability_upgrade_options.remove(upgrade_choice)
                        self._set_ability_score(upgrade_choice, bonus_choice)
                elif bonus_choice == 2:
                    _ok("You may apply a +2 to one ability.")
                    upgrade_choice = prompt(
                        "Which ability do you want to upgrade?",
                        ability_upgrade_options,
                    )
                    self._set_ability_score(upgrade_choice, bonus_choice)
                    _ok(f"Upgraded ability >> {upgrade_choice}")
            elif upgrade_path == "Feat":
                feat_options = get_character_feats()
                feat_options = [
                    x for x in feat_options if x not in self._character["feats"]
                ]

                feat_choice = prompt(
                    "Which feat do you want to acquire?",
                    feat_options,
                )
                _ok(f"Added feat >> {feat_choice}")

                while not self._has_requirements(feat_choice):
                    feat_options.remove(feat_choice)
                    feat_choice = prompt(
                        f"You don't meet the requirements for '{feat_choice}'.",
                        feat_options,
                    )
                else:
                    self._add_feat_perks(feat_choice)
                    self._character["feats"].append(feat_choice)
                    _ok(f"Added feat >> {feat_choice}")

            num_of_upgrades -= 1

    def _set_ability_score(self, ability, bonus=1):
        """Applies a bonus to a specified ability."""
        if not self._is_adjustable(ability, bonus):
            _warn(f"Ability '{ability}' is not adjustable.")
        else:
            new_score = self._character.get("scores").get(ability) + bonus
            self._character["scores"][ability] = new_score
            _ok(f"Ability '{ability}' set to >> {new_score}")
