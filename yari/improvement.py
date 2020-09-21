from collections import OrderedDict
import math
import random
import traceback

from yari.loader import load
from yari.proficiency import get_tool_chest, get_weapon_chest


class ImprovementGenerator:
    """
    Applies ability/feat upgrades to the character (where applicable).

    :param str race: Character's chosen race.
    :param str klass: Character's chosen class.
    :param str subclass: Character's chosen subclass.
    :param int level: Character's chosen level.
    :param dict primary_ability: Primary abilities for the chosen klass.
    :param list saves: Character's proficient saving throws.
    :param str spell_slots: Character's spell slots.
    :param OrderedDict score_array: Character's ability scores.
    :param list languages: Character's languages.
    :param list armor_proficiency: Character's armor proficiencies.
    :param list tool_proficiency: Character's tool proficiencies.
    :param list weapon_proficiency: Character's weapon proficiencies.
    :param list skills: Character's skills.
    :param int upgrade_ratio: Percentage for ability to feat ratio upgrades.

    """

    def __init__(
        self,
        race: str,
        klass: str,
        subclass: str,
        level: int,
        primary_ability: dict,
        saves: list,
        spell_slots: str,
        score_array: OrderedDict,
        languages: list,
        armor_proficiency: list,
        tool_proficiency: list,
        weapon_proficiency: list,
        skills: list,
        upgrade_ratio: int,
    ) -> None:
        self.race = race
        self.klass = klass
        self.subclass = subclass
        self.level = level
        self.saves = saves
        self.spell_slots = spell_slots
        self.score_array = score_array
        self.languages = languages
        self.armor_proficiency = armor_proficiency
        self.tool_proficiency = tool_proficiency
        self.weapon_proficiency = weapon_proficiency
        self.skills = skills
        self.feats = list()

        # Add special class languages (if applicable).
        if klass == "Druid":
            self.languages.append("Druidic")
        elif klass == "Rogue":
            self.languages.append("Thieves' cant")

        # Determine and assign upgrades by ability/feat upgrade ratio.
        upgrade_ratio = self._get_upgrade_ratio(upgrade_ratio)
        if sum(upgrade_ratio) == 0:
            return
        else:
            ability_upgrades = upgrade_ratio[0]
            feat_upgrades = upgrade_ratio[1]
            if ability_upgrades > 0:
                primary_ability = list(primary_ability.values())
                for _ in range(0, ability_upgrades):
                    try:
                        if not self._is_adjustable(primary_ability):
                            raise ValueError("No upgradeable primary abilities.")

                        bonus_applied = random.choice([1, 2])
                        if bonus_applied == 1 and self._is_adjustable(primary_ability):
                            self._set_score(primary_ability[0], bonus_applied)
                            self._set_score(primary_ability[1], bonus_applied)
                        elif bonus_applied == 2 and self._is_adjustable(
                            primary_ability[0]
                        ):
                            self._set_score(primary_ability[0], bonus_applied)
                        elif bonus_applied == 2 and self._is_adjustable(
                            primary_ability[1]
                        ):
                            self._set_score(primary_ability[1], bonus_applied)
                        else:
                            raise ValueError("No upgradeable primary ability by bonus.")
                    except ValueError:
                        self._add_feat()

            if feat_upgrades > 0:
                for _ in range(0, feat_upgrades):
                    self._add_feat()

    def _add_feat(self) -> None:
        """Randomly selects and adds a valid feats."""
        feats = [feat for feat in list(load(file="feats")) if feat not in self.feats]

        # Keep choosing a feat until prerequisites are met.
        random.shuffle(feats)
        feat_choice = feats.pop()
        if not self._has_prerequisites(feat_choice):
            while not self._has_prerequisites(feat_choice):
                random.shuffle(feats)
                feat_choice = feats.pop()
        self._add_features(feat_choice)
        self.feats.append(feat_choice)

    def _add_features(self, feat: str) -> None:
        """
        Assign associated features by specified feat.

        :param str feat: Feat to add features for.

        """
        # Actor
        if feat == "Actor":
            self._set_score("Charisma", 1)

        # Athlete/Lightly Armored/Moderately Armored/Weapon Master
        if feat in (
            "Athlete",
            "Lightly Armored",
            "Moderately Armored",
            "Weapon Master",
        ):
            ability_choice = random.choice(["Strength", "Dexterity"])
            self._set_score(ability_choice, 1)
            if feat == "Lightly Armored":
                self.armor_proficiency.append("Light")
            elif feat == "Moderately Armored":
                self.armor_proficiency.append("Medium")
                self.armor_proficiency.append("Shield")
        # Durable
        if feat == "Durable":
            self._set_score("Constitution", 1)

        # Heavily Armored/Heavy Armor Master
        if feat in ("Heavily Armored", "Heavy Armor Master"):
            self._set_score("Strength", 1)
            if feat == "Heavily Armored":
                self.armor_proficiency.append("Heavy")

        # Keen Mind/Linguist
        if feat in ("Keen Mind", "Linguist"):
            self._set_score("Intelligence", 1)
            if feat == "Linguist":
                # Remove already known languages.
                linguist_languages = [
                    "Abyssal",
                    "Celestial",
                    "Common",
                    "Deep Speech",
                    "Draconic",
                    "Dwarvish",
                    "Elvish",
                    "Giant",
                    "Gnomish",
                    "Goblin",
                    "Halfling",
                    "Infernal",
                    "Orc",
                    "Primordial",
                    "Sylvan",
                    "Undercommon",
                ]
                linguist_languages = [
                    language
                    for language in linguist_languages
                    if language not in self.languages
                ]
                # Choose 3 bonus languages.
                self.languages = self.languages + random.sample(linguist_languages, 3)

        # Observant
        if feat == "Observant":
            if self.klass in ("Cleric", "Druid"):
                self._set_score("Wisdom", 1)
            elif self.klass in ("Wizard",):
                self._set_score("Intelligence", 1)

        # Resilient
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
            ability_choice = random.choice(resilient_saves)
            self._set_score(ability_choice, 1)
            self.saves.append(ability_choice)

        # Skilled
        if feat == "Skilled":
            for _ in range(3):
                skilled_choice = random.choice(["Skill", "Tool"])
                if skilled_choice == "Skill":
                    skills = [
                        skill
                        for skill in list(load(file="skills"))
                        if skill not in self.skills
                    ]
                    self.skills.append(random.choice(skills))
                elif skilled_choice == "Tool":
                    tool_list = [t for t in get_tool_chest()]
                    tool_list = [
                        tool for tool in tool_list if tool not in self.tool_proficiency
                    ]
                    self.tool_proficiency.append(random.choice(tool_list))

        # Tavern Brawler
        if feat == "Tavern Brawler":
            self._set_score(random.choice(["Strength", "Constitution"]), 1)
            self.weapon_proficiency.append("Improvised weapons")
            self.weapon_proficiency.append("Unarmed strikes")

        # Weapon Master
        if feat == "Weapon Master":
            weapons = [t for t in get_weapon_chest()]
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

            self.weapon_proficiency = self.weapon_proficiency + random.sample(
                selections, 4
            )
            selections.clear()

    def _get_upgrade_ratio(self, percentage: int) -> tuple:
        """Returns an 'ability to feat' upgrade ration by percentage."""
        if percentage not in range(0, 101):
            raise ValueError("Argument 'percentage' value must be between 0-100.")
        elif (percentage % 10) != 0:
            raise ValueError("Argument 'percentage' value must be a multiple of 10.")
        else:
            num_of_upgrades = 0
            for _ in range(1, self.level + 1):
                if (_ % 4) == 0 and _ != 20:
                    num_of_upgrades += 1

            if self.klass == "Fighter" and self.level >= 6:
                num_of_upgrades += 1

            if self.klass == "Rogue" and self.level >= 8:
                num_of_upgrades += 1

            if self.klass == "Fighter" and self.level >= 14:
                num_of_upgrades += 1

            if self.level >= 19:
                num_of_upgrades += 1

            percentage = float(percentage)
            ability_upgrades = math.floor(num_of_upgrades * percentage / 100.0)
            feat_upgrades = num_of_upgrades - ability_upgrades
            return ability_upgrades, feat_upgrades

    def _has_prerequisites(self, feat: str) -> bool:
        """
        Determines if character has the prerequisites for a feat.

        :param str feat: Feat to check prerequisites for.

        """
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
        # Chosen feat is "Armored" or Weapon Master but already proficient w/ assoc. armor type.
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

        # Go through ALL additional prerequisites.
        prerequisite = load(feat, file="feats")
        for requirement, _ in prerequisite.items():
            if requirement == "abilities":
                for ability, required_score in prerequisite.get(requirement).items():
                    my_score = self.score_array[ability]
                    if my_score < required_score:
                        return False

            if requirement == "caster":
                # Basic spell caster check, does the character have spells?
                if self.spell_slots == "0":
                    return False

                # Magic Initiative
                if feat == "Magic Initiative" and self.klass not in (
                    "Bard",
                    "Cleric",
                    "Druid",
                    "Sorcerer",
                    "Warlock",
                    "Wizard",
                ):
                    return False

                # Ritual Caster
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
        return True

    def _is_adjustable(self, abilities: (list, tuple, str)) -> bool:
        """
        Determines if an ability can be adjusted i.e: not over 20.

        :param list, tuple, str abilities: Ability score(s) to be checked.

        """
        try:
            if isinstance(abilities, (list, tuple)):
                for ability in abilities:
                    if (self.score_array[ability] + 1) > 20:
                        raise ValueError
            elif isinstance(abilities, str):
                if (self.score_array[abilities] + 2) > 20:
                    raise ValueError
            else:
                raise TypeError(
                    "Argument 'abilities' must be of type list, tuple or str."
                )
        except (KeyError, ValueError):
            return False
        except TypeError:
            traceback.print_exc()
        else:
            return True

    def _set_score(self, ability: str, bonus: int) -> None:
        """
        Adjust a specified ability score with bonus.

        :param str ability: Ability score to set.
        :param int bonus: Value to apply to the ability score.

        """
        try:
            if not isinstance(self.score_array, OrderedDict):
                raise TypeError("Argument 'score_array' must be 'OrderedDict' object.")
            elif ability not in self.score_array:
                raise KeyError(f"Argument 'ability' is invalid: '{ability}'.")
            elif not self._is_adjustable(ability):
                raise ValueError(f"Ability score '{ability}' is not upgradeable.")
            else:
                value = self.score_array.get(ability) + bonus
                self.score_array[ability] = value
        except (KeyError, TypeError):
            traceback.print_exc()
        except ValueError:
            pass
