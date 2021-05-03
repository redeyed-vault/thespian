from argparse import ArgumentParser
from collections import OrderedDict
from dataclasses import dataclass
from random import choice, sample
import traceback
from typing import Dict, List, Type

from parser import Load
from errors import Error
from dice import roll
from httpd import HTTPD
from utils import (
    get_character_backgrounds,
    get_character_classes,
    get_character_feats,
    get_character_races,
    get_proficiency_bonus,
    get_subclasses_by_class,
    get_subraces_by_race,
    prompt,
    sample_choice,
    truncate_dict,
    _e,
)


@dataclass
class _AttributeBuilder:
    """
    Assigns abilities by class, and adds racial bonuses in value/modifier pairs.

    primary_ability dict: Primary class abilities
    racial_bonus dict: Racial ability scores bonus
    threshold int: Required minimum ability score total

    """

    primary_ability: Dict[int, str]
    racial_bonus: Dict[str, int]
    threshold: Type[int] = 65

    def roll(self) -> OrderedDict:
        """
        Generates character's ability scores.

        """

        def determine_ability_scores(threshold: Type[int]) -> List[int]:
            def _roll() -> Type[int]:
                rolls = list(roll("4d6"))
                rolls.remove(min(rolls))
                return sum(rolls)

            results = list()
            while sum(results) < threshold or min(results) < 8 or max(results) < 15:
                results = [_roll() for _ in range(6)]
            return results

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

        # Generate six ability scores
        # Assign primary class abilities first
        # Assign the remaining abilities
        # Apply racial bonuses
        generated_scores = determine_ability_scores(self.threshold)
        for ability in tuple(self.primary_ability.values()):
            value = max(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)
            _e(f"INFO: Ability '{ability}' set to {value}.", "green")
        for _ in range(0, 4):
            ability = choice(ability_choices)
            value = choice(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)
            _e(f"INFO: Ability '{ability}' set to {value}.", "yellow")
        for ability, bonus in self.racial_bonus.items():
            value = score_array.get(ability) + bonus
            score_array[ability] = value
            _e(f"INFO: Bonus of {bonus} applied to '{ability}' ({value}).", "green")

        return score_array


class _CharacterBuilder:
    def __init__(
        self,
        race: Type[str],
        subrace: Type[str],
        klass: Type[str],
        subclass: Type[str],
        level: Type[int],
        sex: Type[str],
        background: Type[str],
    ):
        if level < 3:
            subclass = ""
        if background == "":
            background = Load.get_columns(klass, "background", source_file="classes")

        self.klass = klass
        self.level = level
        self.race = race
        self.sex = sex
        self.subclass = subclass
        self.subrace = subrace
        self.background = background

    def _build_class(
        self, klass: Type[str], subclass: Type[str], level: Type[int], race_data
    ):
        data = Load.get_columns(klass, source_file="classes")
        if data is None:
            raise Error(f"Cannot load class template for '{klass}'.")
        # Remove subclasses entry
        del data["subclasses"]
        # Choose default background if not user-specified
        if self.background == "":
            self.background = data["background"]
        del data["background"]

        for category in (
            "armors",
            "tools",
            "weapons",
        ):
            class_proficiency_list = data[category]
            class_proficiency_list = [
                x for x in class_proficiency_list if x not in race_data[category]
            ]
            data[category] = sample_choice(class_proficiency_list)

        bonus_languages = Load.get_columns(klass, "languages", source_file="classes")
        if len(bonus_languages) != 0:
            bonus_language = bonus_languages[0]
            if bonus_language not in data["languages"]:
                data["languages"].append(bonus_languages)

        if (
            data["spellslots"] is None
            or self.klass in ("Fighter", "Rogue")
            and self.subclass
            not in (
                "Arcane Trickster",
                "Eldritch Knight",
            )
        ):
            data["spellslots"] = "0"
        else:
            data["spellslots"] = data["spellslots"].get(self.level)

        if subclass == "":
            data["features"] = truncate_dict(data["features"], level)
        else:
            subclass_data = Load.get_columns(subclass, source_file="subclasses")
            for feature, value in subclass_data.items():
                if feature in ("armors", "tools", "weapons"):
                    subclass_proficiencies = Load.get_columns(
                        subclass,
                        feature,
                        source_file="subclasses",
                    )
                    for proficiency in subclass_proficiencies:
                        if proficiency not in data[feature]:
                            data[feature].append(proficiency)
                if feature == "bonusmagic":
                    if subclass_data[feature] is None:
                        data[feature] = list()
                        continue
                    bonus_magic = truncate_dict(subclass_data[feature], level)
                    extended_spell_list = list()
                    for spell_list in tuple(bonus_magic.values()):
                        extended_spell_list += spell_list
                    data[feature] = extended_spell_list
                if feature == "features":
                    for level_obtained, feature_list in value.items():
                        if level_obtained in data["features"]:
                            data["features"][level_obtained] += feature_list
                        else:
                            data["features"][level_obtained] = feature_list
                    data["features"] = truncate_dict(data["features"], level)
                if feature == "skills":
                    bonus_skills = subclass_data[feature]
                    if bonus_skills is None:
                        continue
                    if len(bonus_skills) == 1:
                        data[feature] += subclass_data[feature]

        # Calculate hit die/points
        hit_die = int(data["hit_die"])
        data["hitdie"] = f"{self.level}d{hit_die}"
        data["hitpoints"] = hit_die
        if self.level > 1:
            new_level = self.level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            data["hitpoints"] += sum(die_rolls)

        skill_pool = data["skills"]
        background_skills = Load.get_columns(
            self.background, "skills", source_file="backgrounds"
        )
        skill_pool = [
            x
            for x in skill_pool
            if x not in race_data["skills"] and x not in background_skills
        ]
        if klass in ("Rogue",):
            allotment = 4
        elif klass in ("Bard", "Ranger"):
            allotment = 3
        else:
            allotment = 2
        data["skills"] = background_skills
        data["skills"] += sample(skill_pool, allotment)

        return data

    @staticmethod
    def _build_race(race: Type[str], subrace: Type[str], level: Type[int]):
        data = Load.get_columns(race, source_file="races")
        if data is None:
            raise Error(f"Cannot load race template for '{race}'.")

        for category in ("armors", "tools", "weapons"):
            data[category] = sample_choice(data.get(category))

        if subrace != "":
            subrace_data = Load.get_columns(subrace, source_file="subraces")
            if subrace_data is None:
                raise Error(f"Cannot load subrace template for '{subrace}'.")
            for trait, value in subrace_data.items():
                if trait not in data:
                    data[trait] = subrace_data[trait]
                elif trait in (
                    "armors",
                    "languages",
                    "resistances",
                    "skills",
                    "tools",
                    "weapons",
                ):
                    data[trait] += subrace_data[trait]
                elif trait == "bonus":
                    for ability, bonus in value.items():
                        data[trait][ability] = bonus
                elif trait == "darkvision":
                    race_darkvision = data.get(trait)
                    subrace_darkvision = subrace_data.get(trait)
                    if (
                        subrace_darkvision is not None
                        and subrace_darkvision > race_darkvision
                    ):
                        data[trait] = subrace_darkvision
                elif trait == "innatemagic":
                    if data[trait] is None and subrace_data[trait] is None:
                        data[trait] = list()
                        continue
                    else:
                        if data[trait] is None and subrace_data[trait] is not None:
                            data[trait] = subrace_data[trait]
                        innate_spells = data[trait]
                        if len(innate_spells) == 0:
                            continue
                        if type(innate_spells) is list:
                            if len(innate_spells) >= 2:
                                last_value = innate_spells[-1]
                                if isinstance(last_value, int):
                                    del innate_spells[-1]
                                    data[trait] = sample(innate_spells, last_value)
                        elif type(innate_spells) is dict:
                            spell_list = list()
                            innate_spells = truncate_dict(data[trait], level)
                            for _, spells in innate_spells.items():
                                for spell in spells:
                                    spell_list.append(spell)
                            data[trait] = spell_list
                elif trait == "ratio":
                    if data[trait] is None:
                        subrace_ratio = subrace_data[trait]
                        data[trait] = subrace_ratio
                elif trait == "traits":
                    for other in subrace_data.get(trait):
                        data[trait].append(other)

        # Calculate height/weight
        height_base = data.get("ratio").get("height").get("base")
        height_modifier = data.get("ratio").get("height").get("modifier")
        height_modifier = sum(list(roll(height_modifier)))
        weight_base = data.get("ratio").get("weight").get("base")
        weight_modifier = data.get("ratio").get("weight").get("modifier")
        weight_modifier = sum(list(roll(weight_modifier)))
        data["height"] = height_base + height_modifier
        data["weight"] = (height_modifier * weight_modifier) + weight_base
        del data["ratio"]

        return data


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

        def get_feat_requirements(
            feat_name: str, use_local: bool = True
        ) -> (dict, None):
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


class Yari(_CharacterBuilder):
    def __init__(
        self,
        race: Type[str],
        subrace: Type[str],
        klass: Type[str],
        subclass: Type[str],
        level: Type[int] = 1,
        sex: Type[str] = "Female",
        background: Type[str] = "",
    ):
        super(Yari, self).__init__(
            race, subrace, klass, subclass, level, sex, background
        )
        rdata = self._build_race(self.race, self.subrace, self.level)
        cdata = self._build_class(self.klass, self.subclass, self.level, rdata)
        self.abilities = cdata.get("abilities")
        self.ancestor = None
        self.armors = rdata.get("armors") + cdata.get("armors")
        self.bonus = rdata.get("bonus")
        self.bonusmagic = cdata.get("bonusmagic")
        self.darkvision = rdata.get("darkvision")
        self.equipment = cdata.get("equipment")
        self.feats = None
        self.features = cdata.get("features")
        self.height = rdata.get("height")
        self.hitdie = cdata.get("hit_die")
        self.hitpoints = cdata.get("hitpoints")
        self.innatemagic = rdata.get("innatemagic")
        self.languages = rdata.get("languages")
        self.proficiencybonus = get_proficiency_bonus(self.level)
        self.resistances = rdata.get("resistances")
        self.savingthrows = cdata.get("savingthrows")
        self.scores = None
        self.size = rdata.get("size")
        self.skills = cdata.get("skills")
        self.speed = rdata.get("speed")
        self.spellslots = cdata.get("spellslots")
        self.tools = rdata.get("tools") + cdata.get("tools")
        self.traits = rdata.get("traits")
        self.weapons = rdata.get("weapons") + cdata.get("weapons")
        self.weight = rdata.get("weight")

    def run(self):
        for rank, options in self.abilities.items():
            if isinstance(options, list):
                ability_choice = prompt(
                    f"Choose '{self.klass}' class ability",
                    options,
                )
                self.abilities[rank] = ability_choice
        if "random" in self.bonus:
            bonus_ability_count = self.bonus.get("random")
            del self.bonus["random"]
            if not isinstance(bonus_ability_count, int):
                return
            allowed_bonus_abilities = (
                "Strength",
                "Dexterity",
                "Constitution",
                "Intelligence",
                "Wisdom",
                "Charisma",
            )
            bonus_ability_choices = tuple(self.bonus.keys())
            count_limit = len(allowed_bonus_abilities) - len(bonus_ability_choices)
            if bonus_ability_count > count_limit:
                raise Error(
                    "The number of bonus abilities exceeds the number of allowed ability bonuses."
                )
            bonus_ability_choices = [
                x for x in allowed_bonus_abilities if x not in bonus_ability_choices
            ]
            for _ in range(bonus_ability_count):
                message = f"Choose your bonus ability"
                bonus_ability_choice = prompt(message, bonus_ability_choices)
                if bonus_ability_choice in bonus_ability_choices:
                    self.bonus[bonus_ability_choice] = 1
                    bonus_ability_choices.remove(bonus_ability_choice)
        # Dragonborn ancestry prompt
        if self.race == "Dragonborn" and type(self.resistances) is dict:
            dragon_ancestor_options = tuple(self.resistances.keys())
            draconic_ancestry = prompt(
                "Choose your draconic ancestor's type",
                dragon_ancestor_options,
            )
            self.ancestor = draconic_ancestry
            print(f"Draconic ancestor set to '{draconic_ancestry}'.")
            ancestry_resistances = self.resistances
            self.resistances = []
            self.resistances.append(ancestry_resistances.get(draconic_ancestry))
            print(f"Resistances set for '{draconic_ancestry}' ancestry.")

        # Apply and honor all subclass flags
        subclass_flags_options = Load.get_columns(
            self.subclass, "flags", source_file="subclasses"
        )
        subclass_flags = dict()
        if subclass_flags_options != "none":
            flags_finder = subclass_flags_options.split("|")
            for flag_pair in flags_finder:
                key, value = flag_pair.split(",")
                if "&&" in key:
                    flag_options = key.split("&&")
                    if len(flag_options) >= 2:
                        flag_option = prompt(
                            f"'{self.subclass}': Which bonus option do you desire?",
                            flag_options,
                        )
                        subclass_flags[flag_option] = int(value)
                        _e(
                            f"INFO: bonus {flag_option} option chosen for '{self.subclass}' subclass'.",
                            "green",
                        )
                if key not in subclass_flags:
                    subclass_flags[key] = int(value)
        # If none flag is specified, don't bother
        if subclass_flags is None:
            return
        # Iterate through, honoring flags
        for flag, value in subclass_flags.items():
            if flag in ("languages", "skills"):
                acquired_options = None
                if flag == "languages":
                    acquired_options = self.languages
                if flag == "skills":
                    acquired_options = self.skills

                bonus_options = Load.get_columns(
                    self.subclass, flag, source_file="subclasses"
                )
                bonus_options = [x for x in bonus_options if x not in acquired_options]
                if value == -1:
                    acquired_options += bonus_options
                    return

                for _ in range(value):
                    option = prompt(
                        f"Choose bonus {flag} for subclass '{self.subclass}'",
                        bonus_options,
                    )
                    acquired_options.append(option)
                    bonus_options = [
                        x for x in bonus_options if x not in acquired_options
                    ]
                    _e(
                        f"INFO: {flag} '{option}' chosen for subclass '{self.subclass}'.",
                        "green",
                    )

        # Run Attribute generator
        self.scores = _AttributeBuilder(self.abilities, self.bonus).roll()
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


def main():
    app = ArgumentParser(
        prog="Yari", description="Yari: A 5e Dungeons & Dragons character generator."
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
        "-level",
        "-l",
        help="sets character's level",
        type=int,
        choices=tuple(range(1, 21)),
        default=1,
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
        "-alignment",
        "-a",
        help="sets character's alignment",
        type=str,
        choices=(
            "Chaotic Evil",
            "Chaotic Good",
            "Chaotic Neutral",
            "Lawful Evil",
            "Lawful Good",
            "Lawful Neutral",
            "Neutral Evil",
            "Neutral Good",
            "True Neutral",
        ),
        default="True Neutral",
    )
    app.add_argument(
        "-port",
        "-p",
        help="character's output HTTP server port",
        type=int,
        default=8080,
    )
    args = app.parse_args()
    race = args.race
    klass = args.klass
    level = args.level
    sex = args.sex
    alignment = args.alignment
    port = args.port

    subraces = get_subraces_by_race(race)
    if len(subraces) == 0:
        subrace = ""
    else:
        subrace = prompt(f"Choose your '{race}' subrace", subraces)
        if subrace not in subraces:
            subrace = prompt(f"Choose a valid '{race}' subrace", subraces)
        _e(f"INFO: '{race}' subrace '{subrace}' chosen.", "green")

    subclasses = get_subclasses_by_class(klass)
    subclass = prompt(f"Choose your '{klass}' subclass", subclasses)
    if subclass not in subclasses:
        subclass = prompt(f"Choose a valid '{klass}' subclass", subclasses)
    _e(f"INFO: '{klass}' subclass '{subclass}' chosen.", "green")

    background = prompt("Choose your background", get_character_backgrounds())
    _e(f"INFO: 'Character background '{background}' chosen.", "green")

    f = Yari(race, subrace, klass, subclass, level, sex, background)
    f.run()

    print(f.abilities)
    print(alignment)
    print(f.ancestor)
    print(f.armors)
    print(f.background)
    print(f.bonus)
    print(f.bonusmagic)
    print(f.darkvision)
    print(f.equipment)
    print(f.feats)
    print(f.features)
    print(f.height)
    print(f.hitdie)
    print(f.hitpoints)
    print(f.innatemagic)
    print(f.languages)
    print(f.proficiencybonus)
    print(f.resistances)
    print(f.savingthrows)
    print(f.scores)
    print(f.sex)
    print(f.size)
    print(f.skills)
    print(f.speed)
    print(f.spellslots)
    print(f.tools)
    print(f.traits)
    print(f.weapons)
    print(f.weight)

    """
    try:
        with HTTPD(cs) as http:
            http.run(port)
    except (OSError, TypeError, ValueError) as e:
        out(e, 2)
    """
