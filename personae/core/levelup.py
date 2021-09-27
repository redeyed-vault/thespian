from collections import OrderedDict

from .errors import Error
from .seamstress import MyTapestry
from .sources import Load
from .utils import _e, get_character_feats, prompt


class FeatParser:
    """Generates and parses feat characteristic flags by feat."""

    def __init__(self, feat, tapestry):
        self._feat = feat
        self._tapestry = tapestry
        self._perks = Load.get_columns(self._feat, "perk", source_file="feats")

    def _parse_flags(self):
        """Generates flag characteristics for the chosen feat."""
        parsed_flags = dict()
        raw_flags = self._perks.get("flags")
        if raw_flags == "none":
            return parsed_flags

        flag_pairs = raw_flags.split("|")
        for flag_pair in flag_pairs:
            name, increment = flag_pair.split(",")
            if "=" not in name:
                parsed_flags[name] = {"increment": increment}
            else:
                query_string = name.split("=")
                name = query_string[0]
                options = query_string[1].split("&&")
                parsed_flags[name] = {"increment": increment, "options": options}

        return parsed_flags

    def weave(self):
        """Parses flag characteristics for the chosen feat."""

        def is_sub_menu(available_options):
            for opt in available_options:
                if not opt.islower():
                    return False
            return True

        def get_sub_menu_options(available_options):
            if is_sub_menu(available_options):
                sub_options = dict()
                for opt in available_options:
                    sub_options[opt] = Load.get_columns(
                        self._feat, "perk", opt, source_file="feats"
                    )
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
                    raise Error("Malformed parse instructions error.")

            if flag == "ability":
                for _ in range(increment):
                    if len(menu_options) == 1:
                        ability_choice = menu_options[0]
                    else:
                        ability_choice = prompt(
                            "Choose your bonus ability.", menu_options
                        )
                        menu_options.remove(ability_choice)

                bonus_value = self._perks[flag][ability_choice]
                parsed_flag[flag] = (ability_choice, bonus_value)

            elif flag == "proficiency":
                chosen_options = dict()
                submenu_options = None
                for _ in range(increment):
                    menu_choice = prompt(f"Choose your bonus: '{flag}'.", menu_options)
                    if not is_sub_menu(menu_options):
                        menu_options.remove(menu_choice)
                    else:
                        # Generate submenu options, if applicable.
                        if submenu_options is None:
                            submenu_options = get_sub_menu_options(menu_options)
                            submenu_options[menu_choice] = [
                                x
                                for x in submenu_options[menu_choice]
                                if x not in self._tapestry[menu_choice]
                            ]

                        # Create storage for player selctions, if applicable.
                        if len(chosen_options) == 0:
                            for opt in submenu_options:
                                chosen_options[opt] = list()

                        submenu_choice = prompt(
                            f"Choose submenu option: '{menu_choice}'.",
                            submenu_options.get(menu_choice),
                        )
                        chosen_options[menu_choice].append(submenu_choice)
                        submenu_options[menu_choice].remove(submenu_choice)

                for k, v in chosen_options.items():
                    parsed_flag[k] = v

            elif flag in ("armors", "languages", "resistances"):
                if int(options["increment"]) != 0:
                    continue

                parsed_flag[flag] = self._perks[flag]

            elif flag == "speed":
                speed_value = self._perks[flag]
                if speed_value != 0:
                    parsed_flag[flag] = speed_value

        # print(parsed_flag)
        return parsed_flag


class AbilityScoreImprovement:
    """Used to apply ability or feat upgrades to your character."""

    def __init__(self, tapestry):
        self._tapestry = tapestry
        self.ability = tapestry["ability"]
        self.armors = tapestry["armors"]
        self.feats = tapestry["feats"]
        self.klass = tapestry["klass"]
        self.spells = tapestry["spells"]
        self.languages = tapestry["languages"]
        self.level = tapestry["level"]
        self.race = tapestry["race"]
        self.resistances = tapestry["resistances"]
        self.savingthrows = tapestry["savingthrows"]
        self.scores = tapestry["scores"]
        self.skills = tapestry["skills"]
        self.speed = tapestry["speed"]
        self.spellslots = tapestry["spellslots"]
        self.subclass = tapestry["subclass"]
        self.subrace = tapestry["subrace"]
        self.tools = tapestry["tools"]
        self.weapons = tapestry["weapons"]

    def _add_feat_perks(self, feat):
        """Applies feat related perks to the character."""
        a = FeatParser(feat, self._tapestry)
        weave = a.weave()
        if weave is None:
            return

        for flag, options in weave.items():
            if flag == "ability":
                ability, bonus = options
                self._set_ability_score(ability, bonus)
            elif flag == "armors":
                self.armors += options
            elif flag == "languages":
                self.languages += options
            elif flag == "resistances":
                self.resistances += options
            elif flag == "speed":
                self.speed += options
        """
        TODO: Sorting this code out elsewhere.
        # Retrieve all perks for the chosen feat
        for flag, value in perk_flags.items():
            if "save" in perk_flags:
                self.savingthrows.append(ability)
            if flag in (
                "armor",
                "language",
                "resistance",
                "skill",
                "spell",
                "tool",
                "weapon",
            ):
                acquired_options = None
                if flag == "language":
                    acquired_options = self.languages
                if flag == "skill":
                    acquired_options = self.skills
                if flag == "spell":
                    acquired_options = self.spells
                if flag == "tool":
                    acquired_options = self.tools
                if flag == "weapon":
                    acquired_options = self.weapons

                bonus_options = perks.get(flag)
                if isinstance(bonus_options, dict):
                    weapon_options = []
                    if "Simple" in bonus_options and "Simple" in acquired_options:
                        del bonus_options["Simple"]
                    else:
                        weapon_options = weapon_options + bonus_options.get("Simple")
                    if "Martial" in bonus_options and "Martial" in acquired_options:
                        del bonus_options["Martial"]
                    else:
                        weapon_options = weapon_options + bonus_options.get("Martial")
                    bonus_options = weapon_options
                if isinstance(bonus_options, list):
                    for index in range(len(bonus_options)):
                        if type(bonus_options[index]) is not list:
                            continue
                        spell = prompt(
                            f"Choose bonus {flag} for '{feat}' feat",
                            bonus_options[index],
                        )
                        bonus_options[index] = spell
                bonus_options = [x for x in bonus_options if x not in acquired_options]
                if value == -1:
                    acquired_options += bonus_options
                    return
        """

    def _has_required(self, feat):
        def get_feat_requirements(feat_name: str, use_local: bool = True):
            return Load.get_columns(
                feat_name, "required", source_file="feats", use_local=use_local
            )

        # Character already has feat
        if feat in self.feats:
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
            and self.klass == "Monk"
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
            if feat == "Heavily Armored" and "Heavy" in self.armors:
                return False
            elif feat == "Lightly Armored" and "Light" in self.armors:
                return False
            elif feat == "Moderately Armored" and "Medium" in self.armors:
                return False
            elif feat == "Weapon Master" and "Martial" in self.weapons:
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
                    my_score = self.scores[ability]
                    if my_score < required_score:
                        return False

            # Check caster requirements
            if requirement == "caster":
                # If caster prerequisite True
                if prerequisite.get(requirement):
                    # Check if character has spellcasting ability
                    if self.spellslots == "0":
                        return False

                    # Magic Initiative class check
                    if feat == "Magic Initiative" and self.klass not in (
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
                        if armor not in self.armors:
                            return False

            # Check race requirements
            if requirement == "race":
                if self.race not in prerequisite.get(requirement):
                    return False

            # Check subrace requirements
            if requirement == "subrace":
                if self.subrace not in prerequisite.get(requirement):
                    return False

        return True

    def _is_adjustable(self, ability, bonus=1):
        if not isinstance(ability, str):
            raise Error("Argument 'ability' must be of type 'str'.")

        if not isinstance(bonus, int):
            raise Error("Argument 'bonus' must be of type 'int'.")

        if ability not in self.scores:
            raise Error(f"Invalid ability '{ability}' specified.")

        if (self.scores[ability] + bonus) > 20:
            return False

        return True

    def run(self):
        if self.level < 4:
            return

        num_of_upgrades = 0
        for x in range(1, self.level + 1):
            if (x % 4) == 0 and x != 20:
                num_of_upgrades += 1
        if self.klass == "Fighter" and self.level >= 6:
            num_of_upgrades += 1
        if self.klass == "Rogue" and self.level >= 8:
            num_of_upgrades += 1
        if self.klass == "Fighter" and self.level >= 14:
            num_of_upgrades += 1
        if self.level >= 19:
            num_of_upgrades += 1

        while num_of_upgrades > 0:
            if num_of_upgrades > 1:
                _e(f"ASI: You have {num_of_upgrades} upgrades available.", "green")
            else:
                _e("ASI: You have 1 upgrade available.", "green")

            upgrade_path_options = ["Ability", "Feat"]
            upgrade_path = prompt(
                "ASI: Which path do you want to follow?", upgrade_path_options
            )

            # Path #1: Upgrade an Ability.
            # Path #2: Add a new Feat.
            if upgrade_path == "Ability":
                bonus_choice = prompt(
                    "ASI: Do you want an upgrade of a +1 or +2?", ["1", "2"]
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
                    print("ASI: You may apply a +1 to two different abilities.")
                    for _ in range(2):
                        upgrade_choice = prompt(
                            "ASI: Which ability do you want to upgrade?",
                            ability_upgrade_options,
                        )
                        ability_upgrade_options.remove(upgrade_choice)
                        self._set_ability_score(upgrade_choice, bonus_choice)
                elif bonus_choice == 2:
                    print("ASI: You may apply a +2 to one ability.")
                    upgrade_choice = prompt(
                        "ASI: Which ability do you want to upgrade?",
                        ability_upgrade_options,
                    )
                    self._set_ability_score(upgrade_choice, bonus_choice)
                    _e(
                        f"INFO: You have upgraded the ability '{upgrade_choice}'.",
                        "green",
                    )
            elif upgrade_path == "Feat":
                feat_options = get_character_feats()
                feat_options = [x for x in feat_options if x not in self.feats]

                feat_choice = prompt(
                    "ASI: Which feat do you want to acquire?",
                    feat_options,
                )

                while not self._has_required(feat_choice):
                    feat_options.remove(feat_choice)
                    _e(
                        f"INFO: You don't meet the requirements for '{feat_choice}'.",
                        "yellow",
                    )
                    feat_choice = prompt("", feat_options)
                else:
                    self._add_feat_perks(feat_choice)
                    self.feats.append(feat_choice)
                    _e(f"INFO: You have selected the feat '{feat_choice}'.", "green")

            num_of_upgrades -= 1

    def _set_ability_score(self, ability, bonus=1):
        if not self._is_adjustable(ability, bonus):
            _e(f"INFO: Ability '{ability}' is not adjustable.", "yellow")

        new_score = self.scores.get(ability) + bonus
        self.scores[ability] = new_score
        _e(f"INFO: Ability '{ability}' is now set to {new_score}.", "green")
