from collections import OrderedDict
from dataclasses import dataclass
from math import floor
from random import choice, sample, shuffle
import traceback
from typing import Dict, List, Type

from .parser import Load
from ..errors import Error
from ..dice import roll
from ..utils import (
    get_character_feats,
    get_proficiency_bonus,
    prompt,
    sample_choice,
    truncate_dict,
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
        for _ in range(0, 4):
            ability = choice(ability_choices)
            value = choice(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)
        for ability, bonus in self.racial_bonus.items():
            value = score_array.get(ability) + bonus
            score_array[ability] = value

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

        del data["subclasses"]

        if self.background == "":
            self.background = data["background"]

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
                elif feature == "bonusmagic":
                    if subclass_data[feature] is None:
                        data[feature] = list()
                        continue
                    bonus_magic = truncate_dict(subclass_data[feature], level)
                    extended_spell_list = list()
                    for spell_list in tuple(bonus_magic.values()):
                        extended_spell_list += spell_list
                    data[feature] = extended_spell_list
                elif feature == "features":
                    for level_obtained, feature_list in value.items():
                        if level_obtained in data["features"]:
                            data["features"][level_obtained] += feature_list
                        else:
                            data["features"][level_obtained] = feature_list
                    data["features"] = truncate_dict(data["features"], level)
                elif feature == "skills":
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
                        if isinstance(innate_spells, list):
                            if len(innate_spells) >= 2:
                                last_value = innate_spells[-1]
                                if isinstance(last_value, int):
                                    del innate_spells[-1]
                                    data[trait] = sample(innate_spells, last_value)
                        elif isinstance(innate_spells, dict):
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


@dataclass
class _ImprovementGenerator:
    """
    Applies level based upgrades.

    race str: Character's race
    subrace str: Character's subrace (if applicable)
    klass str: Character's class
    subclass str: Character's subclass
    level int: Character's level
    primary_ability dict: Character's primary class abilities
    saves list: Character's saving throws
    magic_innate list: Character's innate magic (if applicable)
    spell_slots str: Character's spell slots
    score_array OrderedDict: Character's ability scores
    languages list: Character's languages
    armor_proficiency list: Character's armor proficiencies
    tool_proficiency list: Character's tool proficiencies
    weapon_proficiency list: Character's weapon proficiencies
    skills list: Character's skills
    feats list: Character's feats
    upgrade_ratio int: Character's ability/feat upgrade ratio

    """

    race: Type[str]
    subrace: Type[str]
    klass: Type[str]
    subclass: Type[str]
    level: Type[int]
    primary_ability: Dict[int, str]
    saves: List[str]
    magic_innate: List[str]
    spell_slots: Type[str]
    score_array: OrderedDict
    languages: List[str]
    armor_proficiency: List[str]
    tool_proficiency: List[str]
    weapon_proficiency: List[str]
    skills: List[str]
    feats: List[str]

    def _add_feat_perks(self, feat: Type[str]) -> None:
        """
        Assign associated features by specified feat

        :param str feat: Feat to add features for

        """

        def get_feat_perks(feat_name: Type[str]) -> (dict, None):
            """Get perks for a feat by feat_name."""
            return Load.get_columns(feat_name, "perk", source_file="feats")

        def has_one(keys: tuple, iterable: tuple) -> bool:
            """Returns True if at least one key is found in iterable."""
            for x in keys:
                if x in iterable:
                    return True
            return False

        # Retrieve all perks for the chosen feat
        perks = get_feat_perks(feat)

        # Feat "ability" perk
        if perks.get("ability") is not None:
            # Retrieve bonus abilities by feat
            feat_ability_options = tuple(perks.get("ability").keys())

            # If Resilient feat selected, treat a upgrade differently
            # Feat offers only one ability option
            # Otherwise feat offers multiple ability options
            if feat == "Resilient":
                # Remove all proficient saving throws.
                resilient_saves = [
                    "Strength",
                    "Dexterity",
                    "Constitution",
                    "Intelligence",
                    "Wisdom",
                    "Charisma",
                ]
                resilient_saves = [
                    save for save in resilient_saves if save not in self.saves
                ]
                # Choose one non-proficient saving throw.
                # Set feat ability score
                # Add ability to proficient saving throws
                ability = sample(resilient_saves, 1)
                self._set_feat_ability(ability)
                self.saves = self.saves + ability
                # Updated Resilient listing with appropriate ability
                # self.feats.remove(feat)
                # self.feats.append(f"{feat} ({ability})")
            elif len(feat_ability_options) == 1:
                chosen_ability = feat_ability_options[0]
                self._set_feat_ability([chosen_ability])
            else:
                # Retrieve primary, secondary class abilities
                class_abilities = tuple(self.primary_ability.values())
                # Store the chosen ability value
                chosen_ability = None
                # If at least one class ability in feat ability options
                # Otherwise just randomly choose one ability
                if has_one(class_abilities, feat_ability_options):
                    for ability in class_abilities:
                        # Ability is one of the feat ability perk options
                        # If ability is adjustable, adjust score
                        # Otherwise, keep it movin'
                        if ability in feat_ability_options:
                            if self._is_adjustable(ability):
                                chosen_ability = ability
                                self._set_feat_ability([chosen_ability])
                                break
                            else:
                                continue
                else:
                    chosen_ability = sample(feat_ability_options, 1)
                    self._set_feat_ability(chosen_ability)

                # If Squat Nimbleness feat chosen
                # Append Athletics skill if Strength chosen
                # Append Acrobatics skill if Dexterity chosen
                # If Strength or Dexterity not class abilities, just choose one
                if feat == "Squat Nimbleness":
                    perk_skills = get_feat_perks(feat).get("skills")
                    chosen_skill = None
                    if "Strength" in class_abilities:
                        chosen_skill = perk_skills[1]
                        self._add_skill(chosen_skill)
                    elif "Dexterity" in class_abilities:
                        chosen_skill = perk_skills[0]
                        self._add_skill(chosen_skill)
                    else:
                        chosen_ability = choice(("Strength", "Dexterity"))
                        if chosen_ability == "Strength":
                            chosen_skill = perk_skills[1]
                            self._add_skill(chosen_skill, perk_skills[0])
                        else:
                            chosen_skill = perk_skills[0]
                            self._add_skill(chosen_skill, perk_skills[1])

        # Feat "language" perk
        if perks.get("language") is not None:
            # Add bonus languages based on feat
            # Add 3 if Linguist feat
            # Add 1 otherwise
            bonus_languages = perks.get("language")
            bonus_languages = [x for x in bonus_languages if x not in self.languages]
            if feat == "Linguist":
                self.languages = self.languages + sample(bonus_languages, 3)
            else:
                self.languages = self.languages + sample(bonus_languages, 1)

        # Feat "proficiency" perk
        if perks.get("proficiency") is not None:
            proficiency_categories = perks.get("proficiency")
            # Armor category, append bonus proficiencies
            # Tool category, append bonus proficiencies
            if "armors" in proficiency_categories:
                self.armor_proficiency = (
                    self.armor_proficiency + proficiency_categories.get("armors")
                )
            elif "tools" in proficiency_categories:
                tool_choice = [
                    x
                    for x in proficiency_categories.get("tools")
                    if x not in self.tool_proficiency
                ]
                self.tool_proficiency.append(choice(tool_choice))
            elif "weapons" in proficiency_categories:

                def get_all_weapons():
                    all_weapons = list()
                    weapons = proficiency_categories.get("weapons")
                    # User has simple weapon proficiencies
                    # Remove all simple weapons from list
                    if "Simple" in self.weapon_proficiency:
                        del weapons["Simple"]

                    # Make an exclusion of non-simple weapons
                    # Make an exclusion of non-martial weapons
                    excluded_weapons = [
                        x
                        for x in self.weapon_proficiency
                        if x != "Simple" and x != "Martial"
                    ]

                    for category, _ in weapons.items():
                        for weapon in weapons.get(category):
                            all_weapons.append(weapon)

                    return all_weapons

                weapons = [x for x in get_weapon_chest()]
                selections = weapons[0]
                # Has Simple weapon proficiency.
                if "Simple" in self.weapon_proficiency:
                    # Has Simple proficiency and tight list of weapon proficiencies.
                    del selections["Simple"]
                    selections = selections.get("Martial")
                    if len(self.weapon_proficiency) > 1:
                        tight_weapon_list = [
                            proficiency
                            for proficiency in self.weapon_proficiency
                            if proficiency != "Simple"
                        ]
                        selections = [
                            selection
                            for selection in selections
                            if selection not in tight_weapon_list
                        ]
                        tight_weapon_list.clear()
                # Doesn't have Simple or Martial proficiency but a tight list of weapons.
                elif "Simple" and "Martial" not in self.weapon_proficiency:
                    selections = selections.get("Martial") + selections.get("Simple")
                    selections = [
                        selection
                        for selection in selections
                        if selection not in self.weapon_proficiency
                    ]

                self.weapon_proficiency = self.weapon_proficiency + sample(
                    selections, 4
                )
                selections.clear()

        # Feat "resistance" perk
        if perks.get("resistance") is not None:
            pass

        # Feat "skills" perk
        if perks.get("skills") is not None:
            pass

        # Feat "spells" perk
        if perks.get("spells") is not None:
            spells = perks.get("spells")
            for spell in spells:
                if isinstance(spell, list):
                    self.magic_innate.append(choice(spell))
                else:
                    self.magic_innate.append(spell)

    def _add_skill(self, skill: Type[str], alternate_skill: Type[str] = None) -> bool:
        """Adds skill or alternate_skill to skill list, (if applicable)."""
        try:
            if skill not in self.skills:
                self.skills.append(skill)
            elif alternate_skill is not None:
                if alternate_skill not in self.skills:
                    self.skills.append(alternate_skill)
                else:
                    raise ValueError("Neither valid skills available")
            return True
        except ValueError:
            return False

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
            if feat == "Heavily Armored" and "Heavy" in self.armor_proficiency:
                return False
            # Character already has light armor proficiency.
            elif feat == "Lightly Armored" and "Light" in self.armor_proficiency:
                return False
            # Character already has medium armor proficiency.
            elif feat == "Moderately Armored" and "Medium" in self.armor_proficiency:
                return False
            # Character already has martial weapon proficiency.
            elif feat == "Weapon Master" and "Martial" in self.weapon_proficiency:
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
                        if armor not in self.armor_proficiency:
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
        print(f"Ability Score Improvement: '{ability}' set to {new_score}.")

    def _set_feat_ability(self, ability_options: list) -> None:
        """
        Adjust a specified ability_array score with bonus.

        :param list ability_options: ability_array score to set.

        """

        def set_ability_score(scores: OrderedDict, ability_name: str):
            # Adjusts the ability score by 1 point
            value = scores.get(ability_name) + 1
            scores[ability_name] = value
            out(f"Feat ability adjustment: '{ability_name}' set to {value}.", -2)

        try:
            # Ensure score_array object is type OrderedDict
            if not isinstance(self.score_array, OrderedDict):
                raise TypeError("Object 'scores' is not type 'OrderedDict'.")

            # If only one ability option available
            if len(ability_options) == 1:
                set_ability_score(self.score_array, ability_options[0])
                return

            is_upgraded = False
            primary_ability = list(self.primary_ability.values())

            # Choose primary ability over other options (if applicable)
            for ability in primary_ability:
                if ability in ability_options:
                    if self._is_adjustable(ability):
                        set_ability_score(self.score_array, ability)
                        is_upgraded = True
                        break
                    else:
                        ability_options.remove(ability)

            # Choose any one ability option if not upgraded above
            if not is_upgraded:
                set_ability_score(self.score_array, choice(ability_options))
        except (KeyError, TypeError):
            traceback.print_exc()

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
                        for _ in range(2):
                            upgrade_choice = prompt(
                                "Choose an ability to upgrade", upgrade_options
                            )
                            upgrade_options.remove(upgrade_choice)
                            self._set_ability_score(upgrade_choice, bonus_choice)
                    elif bonus_choice == 2:
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
                    f"Choose your primary ability for ({self.klass})",
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
        if self.race == "Dragonborn" and isinstance(self.resistances, dict):
            dragon_ancestor_options = tuple(self.resistances.keys())
            draconic_ancestry = prompt(
                "Choose your draconic ancestor's type",
                dragon_ancestor_options,
            )
            self.ancestor = draconic_ancestry
            ancestry_resistances = self.resistances
            self.resistances = []
            self.resistances.append(ancestry_resistances.get(draconic_ancestry))

        self.scores = _AttributeBuilder(self.abilities, self.bonus).roll()

        u = _ImprovementGenerator(
            race=self.race,
            subrace=self.subrace,
            subclass=self.subclass,
            klass=self.klass,
            level=self.level,
            primary_ability=self.abilities,
            saves=self.savingthrows,
            magic_innate=self.innatemagic,
            spell_slots=self.spellslots,
            score_array=self.scores,
            languages=self.languages,
            armor_proficiency=self.armors,
            tool_proficiency=self.tools,
            weapon_proficiency=self.weapons,
            skills=self.skills,
            feats=[],
        )
        u.run()
