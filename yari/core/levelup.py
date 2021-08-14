from collections import OrderedDict

from .errors import Error
from .seamstress import MyTapestry
from .sources import Load
from .utils import _e, get_character_feats, prompt


class FeatFlagParser:
    def __init__(self, feat):
        self._flags = Load.get_columns(feat, "perk", "flags", source_file="feats")
        self._perks = Load.get_columns(feat, "perk", source_file="feats")
        del self._perks["flags"]

    def _parse_flags(self):
        parsed_flags = dict()
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

    def run(self):
        parsed_flags = self._parse_flags()

        # No flags parsed
        if len(parsed_flags) == 0:
            return

        print(parsed_flags)

        for flag, options in parsed_flags.items():
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
                parsed_flags[flag] = {ability_choice: bonus_value}

            if flag == "speed":
                speed_value = self._perks[flag]
                if speed_value != 0:
                    parsed_flags[flag] = speed_value

        print(parsed_flags)


class AbilityScoreImprovement:
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
        self.spellslots = tapestry["spellslots"]
        self.subclass = tapestry["subclass"]
        self.subrace = tapestry["subrace"]
        self.tools = tapestry["tools"]
        self.weapons = tapestry["weapons"]

    def _add_feat_perks(self, feat):
        # Retrieve all perks for the chosen feat
        perks = Load.get_columns(feat, "perk", source_file="feats")
        # Set perk flags, if applicable
        perk_flags = dict()
        if "flags" not in perks or perks.get("flags") == "none":
            perk_flags = None
        else:
            flags_finder = perks.get("flags").split("|")
            for flag_pair in flags_finder:
                key, value = flag_pair.split(",")
                if key not in perk_flags:
                    perk_flags[key] = int(value)
        # If none flag is specified, don't bother
        if perk_flags is None:
            return
        # Iterate through, honoring flags
        for flag, value in perk_flags.items():
            if flag == "ability":
                if value == -1:
                    for ability, bonus in perks.get("ability").items():
                        if self._is_adjustable(ability, bonus):
                            self._set_ability_score(ability, bonus)
                else:
                    ability_choices = list(perks.get("ability").keys())
                    if "save" in perk_flags:
                        ability_choices = [
                            x
                            for x in ability_choices
                            if self._is_adjustable(x, perks.get("ability").get(x))
                            and x not in self.savingthrows
                        ]
                    else:
                        ability_choices = [
                            x
                            for x in ability_choices
                            if self._is_adjustable(x, perks.get("ability").get(x))
                        ]
                    ability = prompt(
                        f"Choose bonus ability for '{feat}' feat", ability_choices
                    )
                    self._set_ability_score(ability, perks.get("ability").get(ability))
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
                if flag == "armor":
                    acquired_options = self.armors
                if flag == "language":
                    acquired_options = self.languages
                if flag == "resistance":
                    acquired_options = self.resistances
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

    def _has_required(self, feat):
        # Character already has feat
        if feat in self.feats:
            return False

        # If Heavily, Lightly, or Moderately Armored feat and a Monk.
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
        # Chosen feat is "Armor Related" or Weapon Master but already proficient w/ assoc. armor type.
        elif feat in (
            "Heavily Armored",
            "Lightly Armored",
            "Moderately Armored",
            "Weapon Master",
        ):
            # Character already has heavy armor proficiency.
            if feat == "Heavily Armored" and "Heavy" in self.armors:
                return False
            # Character already has light armor proficiency.
            elif feat == "Lightly Armored" and "Light" in self.armors:
                return False
            # Character already has medium armor proficiency.
            elif feat == "Moderately Armored" and "Medium" in self.armors:
                return False
            # Character already has martial weapon proficiency.
            elif feat == "Weapon Master" and "Martial" in self.weapons:
                return False

        def get_feat_requirements(feat_name: str, use_local: bool = True):
            return Load.get_columns(
                feat_name, "required", source_file="feats", use_local=use_local
            )

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
            raise Error("First argument 'ability' must be of type 'str'.")

        if ability not in self.scores:
            raise Error(f"Invalid ability '{ability}' specified.")

        if (self.scores[ability] + bonus) > 20:
            return False

        return True

    def _set_ability_score(self, ability, bonus):
        if not isinstance(self.scores, OrderedDict):
            raise Error("Object 'scores' is not type 'OrderedDict'.")

        new_score = self.scores.get(ability) + bonus
        self.scores[ability] = new_score
        _e(f"INFO: Ability '{ability}' is now set to {new_score}.", "green")

    def run(self):
        num_of_upgrades = 0
        if self.level >= 4:
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

        # No upgrades available, we're done here.
        if num_of_upgrades == 0:
            return

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
                        "ASI: Which ability do you want to upgrade?", ability_upgrade_options
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
                    feat_choice = prompt("", feat_options)
                else:
                    self._add_feat_perks(feat_choice)
                    self.feats.append(feat_choice)
                    _e(f"INFO: You have selected the feat '{feat_choice}'.", "green")

            num_of_upgrades -= 1
