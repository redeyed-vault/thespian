from collections import OrderedDict

from .errors import Error
from .seamstress import MyTapestry
from .sources import Load
from .utils import _e, get_character_feats, prompt


class FeatFlagParser:
    """Generates and parses feat characteristic flags by feat."""

    def __init__(self, feat):
        self._flags = Load.get_columns(feat, "perk", "flags", source_file="feats")
        self._perks = Load.get_columns(feat, "perk", source_file="feats")
        del self._perks["flags"]

    def _parse_flags(self):
        """Generates feat flag characteristics."""
        parsed_flags = dict()

        # No flags specified.
        if self._flags == "none":
            return parsed_flags

        flag_pairs = self._flags.split("|")
        for flag_pair in flag_pairs:
            name, increment = flag_pair.split(",")
            if "=" not in name:
                parsed_flags[name] = {"increment": increment}
            else:
                query_string = name.split("=")
                name = query_string[0]
                opts = query_string[1].split("&&")
                parsed_flags[name] = {"increment": increment, "opts": opts}

        return parsed_flags

    def weave(self):
        """Parses feat flag characteristics."""
        final_flag = self._parse_flags()

        # No flags parsed
        if len(final_flag) == 0:
            return

        for flag, options in final_flag.items():
            if flag == "ability":
                increment = options["increment"]
                opts = options["opts"]
                for _ in increment:
                    if len(opts) < 2:
                        ability_choice = opts[0]
                    else:
                        ability_choice = prompt("Choose your bonus ability.", opts)
                        opts.remove(ability_choice)

                bonus_value = self._perks[flag][ability_choice]
                final_flag[flag] = (ability_choice, bonus_value)
            elif flag in ("armors", "languages", "resistances"):
                increment = int(options["increment"])
                if increment <= 1:
                    final_flag[flag] = self._perks[flag]
                else:
                    # TODO: Impementing multiple choices
                    chosen_options = list()  # pylint: disable=unused-variable
                    available_options = self._perks[flag]
                    print(available_options)
            elif flag == "speed":
                speed_value = self._perks[flag]
                if speed_value != 0:
                    final_flag[flag] = speed_value

        return final_flag


class AbilityScoreImprovement:
    """Used to apply ability or feat upgrades to your character."""

    def __init__(self, tapestry):
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
        a = FeatFlagParser(feat)
        weave = a.weave()

        # No weave created
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

                for _ in range(value):
                    option = prompt(
                        f"Choose bonus {flag} for '{feat}' feat", bonus_options
                    )
                    acquired_options.append(option)
                    bonus_options = [
                        x for x in bonus_options if x not in acquired_options
                    ]
                    _e(f"INFO: {flag} '{option}' chosen.", "green")
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
        # No upgrades available, we're done here.
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
                print(f"ASI: You have {num_of_upgrades} upgrades available.")
            else:
                print("ASI: You have 1 upgrade available.")

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
