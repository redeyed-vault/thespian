from argparse import ArgumentParser
from collections import OrderedDict
import traceback
from typing import List, Type

from .errors import Error
from .dice import roll
from .httpd import HTTPD
from .sources import Load
from .utils import (
    get_character_classes,
    get_character_feats,
    get_character_races,
    prompt,
    _e,
)


class _ImprovementGenerator:
    def __init__(
        self,
        armors: List[str],
        feats: List[str],
        klass: Type[str],
        innatemagic: List[str],
        languages: List[str],
        level: Type[int],
        race: Type[str],
        resistances: List[str],
        saves: List[str],
        score_array: OrderedDict,
        skills: List[str],
        spell_slots: Type[str],
        subclass: Type[str],
        subrace: Type[str],
        tools: List[str],
        weapons: List[str],
    ):
        self.armors = armors
        self.feats = feats
        self.klass = klass
        self.innatemagic = innatemagic
        self.languages = languages
        self.level = level
        self.race = race
        self.resistances = resistances
        self.saves = saves
        self.score_array = score_array
        self.skills = skills
        self.spell_slots = spell_slots
        self.subclass = subclass
        self.subrace = subrace
        self.tools = tools
        self.weapons = weapons

    def _add_feat_perks(self, feat: Type[str]) -> None:
        """
        Assign associated features by specified feat

        :param str feat: Feat to add features for

        """
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
                            and x not in self.saves
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
                        self.saves.append(ability)
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
                    acquired_options = self.innatemagic
                if flag == "tool":
                    acquired_options = self.tools
                if flag == "weapon":
                    acquired_options = self.weapons

                bonus_options = perks.get(flag)
                if type(bonus_options) is dict:
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
                if type(bonus_options) is list:
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

    def _has_required(self, feat: Type[str]) -> bool:
        """
        Determines if character has the prerequisites for feat.

        :param str feat: Feat to check prerequisites for.

        """
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
            """Returns all requirements for feat_name."""
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
                    my_score = self.score_array[ability]
                    if my_score < required_score:
                        return False

            # Check caster requirements
            if requirement == "caster":
                # If caster prerequisite True
                if prerequisite.get(requirement):
                    # Check if character has spellcasting ability
                    if self.spell_slots == "0":
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

                    # Ritual Caster class check
                    if feat == "Ritual Caster":
                        my_score = 0
                        required_score = 0
                        if self.klass in ("Cleric", "Druid"):
                            my_score = self.score_array.get("Wisdom")
                            required_score = prerequisite.get("abilities").get("Wisdom")
                        elif self.klass == "Wizard":
                            my_score = self.score_array.get("Intelligence")
                            required_score = prerequisite.get("abilities").get(
                                "Intelligence"
                            )

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

    def _is_adjustable(self, ability: Type[str], bonus: Type[int] = 1) -> bool:
        """
        Determines if an ability can be adjusted i.e: not over 20.

        :param str abilities:
        :param int bonus:

        """
        try:
            if isinstance(ability, str):
                if (self.score_array[ability] + bonus) > 20:
                    raise ValueError
            else:
                raise RuntimeError
        except RuntimeError:
            traceback.print_exc()
        except ValueError:
            return False
        return True

    def _set_ability_score(self, ability: Type[str], bonus: Type[int]) -> None:
        """
        Adjust a specified ability_array score with bonus.

        :param list ability:
        :param list bonus

        """
        try:
            if not isinstance(self.score_array, OrderedDict):
                raise TypeError("Object 'score_array' is not type 'OrderedDict'.")
        except (KeyError, TypeError):
            traceback.print_exc()
        new_score = self.score_array.get(ability) + bonus
        self.score_array[ability] = new_score
        _e(f"INFO: Ability '{ability}' is now set to {new_score}.", "green")

    def run(self):
        """
        Runs character upgrades (if applicable).

        """
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
        if num_of_upgrades == 0:
            return
        while num_of_upgrades > 0:
            if num_of_upgrades > 1:
                print(f"You have {num_of_upgrades} upgrades available.")
            else:
                print(f"You have 1 upgrade available")
            upgrade_path_options = ["Ability", "Feat"]
            upgrade_path = prompt("Choose your upgrade path", upgrade_path_options)
            if upgrade_path in upgrade_path_options:
                if upgrade_path == "Ability":
                    bonus_choice = prompt("Choose bonus value", ["1", "2"])
                    upgrade_options = (
                        "Strength",
                        "Dexterity",
                        "Constitution",
                        "Intelligence",
                        "Wisdom",
                        "Charisma",
                    )
                    bonus_choice = int(bonus_choice)
                    upgrade_options = [
                        x
                        for x in upgrade_options
                        if self._is_adjustable(x, bonus_choice)
                    ]
                    if bonus_choice == 1:
                        print("You may apply a bonus of 1 to two abilities.")
                        for _ in range(2):
                            upgrade_choice = prompt(
                                "Choose an ability to upgrade", upgrade_options
                            )
                            upgrade_options.remove(upgrade_choice)
                            self._set_ability_score(upgrade_choice, bonus_choice)
                    elif bonus_choice == 2:
                        print("You may apply a bonus of 2 to one ability.")
                        upgrade_choice = prompt(
                            "Choose an ability to upgrade", upgrade_options
                        )
                        self._set_ability_score(upgrade_choice, bonus_choice)
                elif upgrade_path == "Feat":
                    feat_list = get_character_feats()
                    filtered_feat_options = [
                        x
                        for x in feat_list
                        if self._has_required(x) and x not in self.feats
                    ]
                    feat_choice = prompt(
                        "Choose a feat",
                        filtered_feat_options,
                    )
                    self._add_feat_perks(feat_choice)
                    self.feats.append(feat_choice)
                num_of_upgrades -= 1


def main():
    app = ArgumentParser(
        prog="Yari", description="A Dungeons & Dragons 5e character generator."
    )
    app.add_argument(
        "-race",
        "-r",
        help="sets character's race",
        required=True,
        type=str,
        choices=get_character_races(),
        default="Human",
    )
    app.add_argument(
        "-klass",
        "-k",
        help="sets character's class",
        type=str,
        choices=get_character_classes(),
        default="Fighter",
    )
    app.add_argument(
        "-sex",
        "-s",
        help="sets character's sex",
        type=str,
        choices=("Female", "Male"),
        default="Female",
    )
    app.add_argument(
        "-port",
        "-p",
        help="sets HTTP server port",
        type=int,
        default=8080,
    )
    args = app.parse_args()
    race = args.race
    klass = args.klass
    sex = args.sex
    port = args.port

    from .flags import RaceSeamstress, ClassSeamstress, AttributeGenerator, MyTapestry

    # Generate racial and class attributes
    a = RaceSeamstress(race, sex)
    b = ClassSeamstress(klass, a.data)

    # Run Attribute generator
    a.data["scores"] = AttributeGenerator(
        b.data.get("ability"), a.data.get("bonus")
    ).roll()

    """
    # Run Ability Score Improvement generator
    u = _ImprovementGenerator(
        armors=self.armors,
        feats=[],
        klass=self.klass,
        innatemagic=self.innatemagic,
        languages=self.languages,
        level=self.level,
        race=self.race,
        resistances=self.resistances,
        saves=self.savingthrows,
        score_array=self.scores,
        skills=self.skills,
        spell_slots=self.spellslots,
        subclass=self.subclass,
        subrace=self.subrace,
        tools=self.tools,
        weapons=self.weapons,
    )
    u.run()
    self.armors = u.armors
    self.feats = u.feats
    self.innatemagic = u.innatemagic
    self.languages = u.languages
    self.resistances = u.resistances
    self.tools = u.tools
    self.weapons = u.weapons
    """

    # Load final character tapestry
    c = MyTapestry()
    c.sew_tapestry(a.data, b.data)
    try:
        with HTTPD(c.view(), port) as http:
            http.run()
    except (OSError, TypeError, ValueError) as e:
        pass
