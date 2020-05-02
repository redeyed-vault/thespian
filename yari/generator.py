from collections import OrderedDict
from math import ceil
import random

from yari.reader import reader


# ATTRIBUTE GENERATOR
class _Bonuses:
    """Determines ability bonuses by race and subrace (if applicable)."""

    def __init__(
        self, race: str, variant: bool, class_attr: dict, subrace=None
    ) -> None:
        """
        Args:
            race (str): Character's race.
            variant (bool): Use variant rules.
            class_attr (tuple): Character's primary abilities.
            subrace (str, None): Character's subrace (if applicable).       
        """
        bonuses = dict()
        class_attr = list(class_attr.values())
        # Half-elf ability bonuses.
        if race == "HalfElf":
            ability_choices = [
                "Strength",
                "Dexterity",
                "Constitution",
                "Intelligence",
                "Wisdom",
            ]
            if "Charisma" in class_attr:
                class_attr.remove("Charisma")
                # Get the remaining primary ability, assign the bonus.
                saved_ability = pick(class_attr)
                bonuses[saved_ability] = 1
                # Remove the remaining ability from the choices.
                ability_choices.remove(saved_ability)
                # Choose third ability.
                bonuses[pick(ability_choices)] = 1
            else:
                for ability in class_attr:
                    bonuses[ability] = 1
        # Non-human or human non-variant ability bonuses.
        elif race == "Human" and not variant or race != "Human":
            racial_bonuses = reader("races", (race, "traits", "abilities"))
            for ability, bonus in racial_bonuses.items():
                bonuses[ability] = bonus
        # Human variant bonuses.
        elif race == "Human" and variant:
            racial_bonuses = class_attr
            for ability in racial_bonuses:
                bonuses[ability] = 1

        if subrace is not None:
            if subrace in get_subraces_by_race(race):
                subracial_bonuses = reader("subraces", (subrace, "traits", "abilities"))
                for ability, bonus in subracial_bonuses.items():
                    bonuses[ability] = bonus
        self.bonuses = bonuses


class AbilityScoreGenerator(_Bonuses):
    """Assigns ability scores/bonuses by primary abilities."""

    def __init__(
        self, race: str, class_attr: dict, variant: bool, subrace=None
    ) -> None:
        """
        Args:
            race (str): Character's race.
            class_attr (dict): Class primary abilities.
            variant (bool): Use variant rules.
            subrace (str, None): Character's subrace (if applicable).
        """
        super().__init__(race, variant, class_attr, subrace)
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

        generated_scores = self.roll_ability_scores(60)
        # Assign highest values to class specific abilities first.
        for ability in tuple(class_attr.values()):
            value = max(generated_scores)
            modifier = get_ability_modifier(value)
            score_array[ability] = OrderedDict({"Value": value, "Modifier": modifier})
            ability_choices.remove(ability)
            generated_scores.remove(value)

        # Assign remaining abilities/scores.
        for _ in range(0, 4):
            ability = random.choice(ability_choices)
            value = random.choice(generated_scores)
            modifier = get_ability_modifier(value)
            score_array[ability] = OrderedDict({"Value": value, "Modifier": modifier})
            ability_choices.remove(ability)
            generated_scores.remove(value)

        # Apply racial bonuses.
        for ability, bonus in self.bonuses.items():
            value = score_array.get(ability).get("Value") + bonus
            modifier = get_ability_modifier(value)
            score_array[ability] = OrderedDict({"Value": value, "Modifier": modifier})
        self.score_array = score_array

    @staticmethod
    def roll_ability_scores(threshold: int) -> list:
        """Generates six ability scores."""

        def roll() -> list:
            """Returns random list between 1-6 x4."""
            rst = list()
            for _ in range(0, 4):
                rst.append(random.randint(1, 6))
            return rst

        results = list()
        while sum(results) < threshold:
            for _ in range(0, 6):
                result = roll()
                results.append(sum(result) - min(result))

            score_total = sum(results)
            maximum_score = max(results)
            minimum_score = min(results)

            if score_total < threshold or maximum_score < 15 or minimum_score < 8:
                results = list()
        return results


def get_ability_modifier(score: int) -> int:
    """Returns ability modifier by score."""
    return score is not 0 and int((score - 10) / 2) or 0


def get_proficiency_bonus(level: int) -> int:
    """Returns a proficiency bonus value by level."""
    return ceil((level / 4) + 1)


# CHARACTER CLASS GENERATOR
class _Features:
    """DO NOT call class directly. Used to generate class features.
    Inherited in another class.

    Inherited by the following classes:

        - Barbarian
        - Bard
        - Cleric
        - Druid
        - Fighter
        - Monk
        - Paladin
        - Ranger
        - Rogue
        - Sorcerer
        - Warlock
        - Wizard

    """

    def __init__(self, **kw) -> None:
        """
        Args:
            kw:
                - level (int): Character's chosen level.
                - path (str): Character's chosen path.
                - roll_hp (bool): True: Roll or False: use default HP by class/level.
        """
        self.class_ = self.__class__.__name__
        if self.class_ == "_Features":
            raise Exception("this class must be inherited")

        if not get_is_class(self.class_):
            raise ValueError("class '{}' does not exist".format(self.class_))

        if "level" not in kw or not isinstance(kw["level"], int):
            kw["level"] = 1

        if "path" not in kw or not get_is_path(kw["path"], self.class_):
            kw["path"] = None

        if "roll_hp" not in kw or not isinstance(kw["roll_hp"], bool):
            kw["roll_hp"] = False

        self.level = kw.get("level")
        self.path = kw.get("path")
        self.roll_hp = kw.get("roll_hp")

        self.features = reader("classes", (self.class_,))
        self.features["abilities"] = self._enc_class_abilities()
        self.features["features"] = self._enc_class_features()
        self.features["path"] = self.path
        if (
            self.class_ == "Fighter"
            and self.path != "Eldritch Knight"
            or self.class_ == "Rogue"
            and self.path != "Arcane Trickster"
        ):
            self.features["spell_slots"] = ""
        else:
            self.features["spell_slots"] = self.features["spell_slots"].get(self.level)

        if has_class_spells(self.path):
            self._enc_class_magic_list()

        self._enc_class_hit_die()
        self._enc_class_proficiency("armors")
        self._enc_class_proficiency("tools")
        self._enc_class_proficiency("weapons")

        del self.features["paths"]

    def _enc_class_abilities(self):
        a_list = reader("classes", (self.class_, "abilities",))
        if self.class_ == "Cleric":
            a_list[2] = random.choice(a_list[2])
        elif self.class_ in ("Fighter", "Ranger"):
            ability_choices = a_list.get(1)
            a_list[1] = random.choice(ability_choices)
            if self.class_ == "Fighter" and self.path != "Eldritch Knight":
                a_list[2] = "Constitution"
            elif self.class_ == "Fighter" and self.path == "Eldritch Knight":
                a_list[2] = "Intelligence"
            else:
                a_list[2] = a_list.get(2)
        elif self.class_ == "Rogue":
            if self.path != "Arcane Trickster":
                a_list[2] = "Charisma"
            else:
                a_list[2] = "Intelligence"
        elif self.class_ == "Wizard":
            ability_choices = a_list.get(2)
            a_list[2] = random.choice(ability_choices)
        return a_list

    def _enc_class_features(self):
        """Builds a dictionary of features by class, path & level."""
        final_feature_list = dict()
        feature_list = reader("classes", (self.class_,)).get("features")
        path_feature_list = reader("paths", (self.path,)).get("features")

        for level in range(1, self.level + 1):
            feature_row = list()
            if level in feature_list:
                fuse(feature_row, feature_list[level])
            if level in path_feature_list:
                fuse(feature_row, path_feature_list[level])
            if len(feature_row) is not 0:
                final_feature_list[level] = feature_row

        return final_feature_list

    def _enc_class_hit_die(self):
        hit_die = self.features.get("hit_die")
        self.features["hit_die"] = f"{self.level}d{hit_die}"
        self.features["hit_points"] = hit_die
        if self.level > 1:
            new_level = self.level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                if self.roll_hp:
                    hp_result = random.randint(1, hit_die)
                else:
                    hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            self.features["hit_points"] += sum(die_rolls)

    def _enc_class_magic_list(self):
        """Builds a dictionary list of specialized magic spells."""
        magic = dict()
        class_magic = reader("paths", (self.path,)).get("magic")

        if len(class_magic) is not 0:
            for level, spells in class_magic.items():
                if level <= self.level:
                    magic[level] = spells

            del class_magic
            self.features["magic"] = magic

    def _enc_class_proficiency(self, prof_type: str):
        class_proficiency = reader("classes", (self.class_, "proficiency"))
        path_proficiency = reader("paths", (self.path, "proficiency"))
        if prof_type not in ("armors", "tools", "weapons"):
            raise ValueError

        if prof_type == "tools":
            if self.path == "Assassin" and self.level < 3:
                return
            elif self.class_ == "Monk":
                monk_bonus_tool = random.choice(class_proficiency[prof_type])
                class_proficiency[prof_type] = [monk_bonus_tool]
        elif (
            prof_type == "weapons"
            and self.path == "College of Valor"
            and self.level < 3
        ):
            return
        else:
            path_list = path_proficiency[prof_type]
            if len(path_list) is not 0:
                for proficiency in path_list:
                    class_proficiency[prof_type].append(proficiency)
                class_proficiency[prof_type].sort()
        self.features["proficiency"][prof_type] = class_proficiency[prof_type]


class Barbarian(_Features):
    def __init__(self, **kw) -> None:
        super(Barbarian, self).__init__(**kw)


class Bard(_Features):
    def __init__(self, **kw) -> None:
        super(Bard, self).__init__(**kw)


class Cleric(_Features):
    def __init__(self, **kw) -> None:
        super(Cleric, self).__init__(**kw)


class Druid(_Features):
    def __init__(self, **kw) -> None:
        super(Druid, self).__init__(**kw)


class Fighter(_Features):
    def __init__(self, **kw) -> None:
        super(Fighter, self).__init__(**kw)


class Monk(_Features):
    def __init__(self, **kw) -> None:
        super(Monk, self).__init__(**kw)


class Paladin(_Features):
    def __init__(self, **kw) -> None:
        super(Paladin, self).__init__(**kw)


class Ranger(_Features):
    def __init__(self, **kw) -> None:
        super(Ranger, self).__init__(**kw)


class Rogue(_Features):
    def __init__(self, **kw) -> None:
        super(Rogue, self).__init__(**kw)


class Sorcerer(_Features):
    def __init__(self, **kw) -> None:
        super(Sorcerer, self).__init__(**kw)


class Warlock(_Features):
    def __init__(self, **kw) -> None:
        super(Warlock, self).__init__(**kw)


class Wizard(_Features):
    def __init__(self, **kw) -> None:
        super(Wizard, self).__init__(**kw)


def get_is_class(class_) -> bool:
    return class_ in tuple(reader("classes").keys())


def get_is_path(path, class_) -> bool:
    return path in tuple(reader("classes", (class_, "paths")))


def get_paths_by_class(class_) -> tuple:
    return tuple(reader("classes", (class_, "paths")))


def has_class_spells(path) -> bool:
    class_spells = reader("paths", (path,)).get("magic")
    return len(class_spells) is not 0


# CHARACTER IMPROVEMENT GENERATOR
class ImprovementGenerator:
    """Determines/applies feats and ability upgrades (if applicable)."""

    def __init__(
        self,
        race: str,
        klass: str,
        path: str,
        level: int,
        class_attr: dict,
        saves: list,
        spell_slots: str,
        score_array: OrderedDict,
        languages: list,
        armor_proficiency: list,
        tool_proficiency: list,
        weapon_proficiency: list,
        skills: list,
        variant: bool,
    ) -> None:
        """
        Args:
            race (str): Character's race.
            klass (str): Character's class.
            level (int): Character's level.
            class_attr (dict): Primary abilities for class_.
            saves (list): Character's proficient saving throws.
            spell_slots (str): Character's spell slots.
            score_array (OrderedDict): Character's ability scores.
            languages (list): Character's languages.
            armor_proficiency (list): Character's armor proficiencies.
            tool_proficiency (list): Character's tool proficiencies.
            weapon_proficiency (list): Character's weapon proficiencies.
            skills (list): Character's skills.
            variant (bool): Use variant rules.
        """
        self.klass = klass
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

        # Human and variant rules are used, give bonus feat.
        if race == "Human" and variant:
            self.add_feat()

        # Add special class languages (if applicable).
        if klass == "Druid":
            self.languages.append("Druidic")

        if klass == "Rogue":
            self.languages.append("Thieves' cant")

        # Bards in the College of Lore get three bonus skills at level 3.
        if path == "College of Lore" and level >= 3:
            all_skills = get_all_skills()
            purge(all_skills, self.skills)
            fuse(self.skills, random.sample(all_skills, 3))

        # Determine number of applicable upgrades
        upgrades = 0
        for _ in range(1, level + 1):
            if (_ % 4) == 0 and _ is not 20:
                upgrades += 1

        if klass == "Fighter" and level >= 6:
            upgrades += 1

        if klass == "Rogue" and level >= 8:
            upgrades += 1

        if klass == "Fighter" and level >= 14:
            upgrades += 1

        if level >= 19:
            upgrades += 1

        # Cycle through the available upgrades (if applicable)
        if upgrades is 0:
            return

        class_attr = list(class_attr.values())
        for _ in range(1, upgrades):
            if len(class_attr) is 0:
                upgrade_option = "Feat"
            else:
                upgrade_option = random.choice(["Ability", "Feat"])

            if upgrade_option == "Ability":
                try:
                    if len(class_attr) is 2:
                        if self.isadjustable(class_attr):
                            for ability in class_attr:
                                self.set_score_array(ability, 1)
                                if not self.isadjustable(ability):
                                    class_attr.remove(ability)
                        elif len(class_attr) is 1:
                            ability = class_attr[0]
                            if self.isadjustable(ability):
                                self.set_score_array(ability, 2)
                                if not self.isadjustable(ability):
                                    class_attr.remove(ability)
                        else:
                            raise ValueError
                    else:
                        raise ValueError
                except ValueError:
                    upgrade_option = "Feat"

            if upgrade_option == "Feat":
                self.feats.append(self.add_feat())

    def add_feat(self) -> str:
        feats = list(reader("feats").keys())
        # Remove feats already possessed by the character
        purge(feats, self.feats)
        feat_choice = pick(feats)

        # Keep choosing a feat until prerequisites are met
        if not self.has_feat_prerequisites(feat_choice):
            while not self.has_feat_prerequisites(feat_choice):
                feat_choice = pick(feats)
        self.add_features(feat_choice)
        return feat_choice

    def add_features(self, feat: str) -> None:
        """Assign associated features by specified feat."""
        # Actor
        if feat == "Actor":
            self.set_score_array("Charisma", 1)

        # Athlete/Lightly Armored/Moderately Armored/Weapon Master
        if feat in (
            "Athlete",
            "Lightly Armored",
            "Moderately Armored",
            "Weapon Master",
        ):
            ability_choice = random.choice(["Strength", "Dexterity"])
            self.set_score_array(ability_choice, 1)
            if feat == "Lightly Armored":
                add(self.armor_proficiency, "Light")
            elif feat == "Moderately Armored":
                add(self.armor_proficiency, "Medium")
                add(self.armor_proficiency, "Shield")
        # Durable
        if feat == "Durable":
            self.set_score_array("Constitution", 1)

        # Heavily Armored/Heavy Armor Master
        if feat in ("Heavily Armored", "Heavy Armor Master"):
            self.set_score_array("Strength", 1)
            if feat == "Heavily Armored":
                add(self.armor_proficiency, "Heavy")

        # Keen Mind/Linguist
        if feat in ("Keen Mind", "Linguist"):
            self.set_score_array("Intelligence", 1)
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
                purge(linguist_languages, self.languages)
                # Choose 3 bonus languages.
                fuse(self.languages, random.sample(linguist_languages, 3))

        # Observant
        if feat == "Observant":
            if self.klass in ("Cleric", "Druid"):
                self.set_score_array("Wisdom", 1)
            elif self.klass in ("Wizard",):
                self.set_score_array("Intelligence", 1)

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
            purge(resilient_saves, self.saves)
            # Choose one non-proficient saving throw.
            ability_choice = random.choice(resilient_saves)
            self.set_score_array(ability_choice, 1)
            add(self.saves, ability_choice)

        # Skilled
        if feat == "Skilled":
            for _ in range(3):
                skilled_choice = random.choice(["Skill", "Tool"])
                if skilled_choice == "Skill":
                    skill_list = list(reader("skills").keys())
                    skills = purge(skill_list, self.skills)
                    add(self.skills, random.choice(skills))
                elif skilled_choice == "Tool":
                    tool_list = list()
                    for main_tool, sub_tools in reader("tools").items():
                        if main_tool in (
                            "Artisan's tools",
                            "Gaming tools",
                            "Musical instrument",
                        ):
                            for sub_tool in sub_tools:
                                sub_tool = f"{main_tool} - {sub_tool}"
                                tool_list.append(sub_tool)
                        else:
                            tool_list.append(main_tool)
                    purge(tool_list, self.tool_proficiency)
                    add(self.tool_proficiency, random.choice(tool_list))

        # Tavern Brawler
        if feat == "Tavern Brawler":
            self.set_score_array(random.choice(["Strength", "Constitution"]), 1)
            add(self.weapon_proficiency, "Improvised weapons")
            add(self.weapon_proficiency, "Unarmed strikes")

        # Weapon Master
        if feat == "Weapon Master":
            weapons = reader("weapons", "Martial")
            if "Simple" not in self.weapon_proficiency:
                fuse(weapons, reader("weapons", "Simple"))

            for weapon in self.weapon_proficiency:
                if weapon in ("Simple", "Martial"):
                    continue

                if weapon in weapons:
                    weapons.remove(weapon)

            bonus_weapons = random.sample(weapons, 4)
            for weapon in bonus_weapons:
                add(self.weapon_proficiency, weapon)

    def expand_saving_throws(self) -> list:
        """Adds detailed saving throw details (associated score/modifier)."""
        es = list()
        for save in self.saves:
            ability_score = self.score_array.get(save).get("Value")
            ability_modifier = get_ability_modifier(ability_score)
            save_value = get_proficiency_bonus(self.level) + ability_modifier
            es.append((save, save_value))
        return es

    def has_feat_prerequisites(self, feat: str) -> bool:
        """Determines if character has the prerequisites for a feat."""
        # If character already has feat.
        if feat in self.feats:
            return False

        # If Heavily, Lightly, or Moderately Armored feat and a Monk.
        if (
            feat in ("Heavily Armored", "Lightly Armored", "Moderately Armored",)
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
        prq = reader("feats", (feat,))
        for requirement, _ in prq.items():
            if requirement == "abilities":
                for ability, required_score in prq.get("abilities").items():
                    my_score = self.score_array[ability]["Value"]
                    if my_score < required_score:
                        return False

            if requirement == "caster":
                # Basic spell caster check, does the character have spells?
                if self.spell_slots == "":
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
                        my_score = self.score_array["Wisdom"]["Value"]
                        required_score = prq.get("abilities").get("Wisdom")
                    elif self.klass == "Wizard":
                        my_score = self.score_array["Intelligence"]["Value"]
                        required_score = prq.get("abilities").get("Intelligence")

                    if my_score < required_score:
                        return False
        return True

    def isadjustable(self, abilities: (list, str)) -> (bool, int):
        """Determines if an ability can be adjusted i.e: not over 20"""
        if isinstance(abilities, list):
            for ability in abilities:
                cur_value = self.score_array.get(ability).get("Value")
                if (cur_value + 1) > 20:
                    return False
        elif isinstance(abilities, str):
            for bonus in (2, 1):
                cur_value = self.score_array.get(abilities).get("Value")
                if (cur_value + bonus) <= 20:
                    return bonus
            return False
        return True

    def set_score_array(self, ability: str, bonus: int) -> None:
        """Adjust a specified ability with bonus."""
        if not isinstance(self.score_array, OrderedDict):
            raise TypeError("argument 'score_array' must be 'OrderedDict' object")
        value = self.score_array[ability]["Value"] + bonus
        modifier = get_ability_modifier(value)
        self.score_array[ability] = OrderedDict({"Value": value, "Modifier": modifier})


# CHARACTER PROFICIENCY GENERATOR
class ProficiencyGenerator:
    """Merges class with racial proficiencies (if applicable)."""

    def __init__(self, prof_type: str, features: dict, traits: dict) -> None:
        """
        Args:
            prof_type (str): Defines proficiency type (armors|tools|weapons).
            features (dict): Gets class proficiency by prof_type.
            traits (dict): Gets racial proficiency by prof_type (if applicable).
        """
        if prof_type not in ("armors", "tools", "weapons"):
            raise ValueError(f"error: invalid 'prof_type' argument '{prof_type}'")
        else:
            class_proficiency = features.get("proficiency").get(prof_type)
            if "proficiency" in traits:
                trait_proficiency = traits.get("proficiency")
                if prof_type in trait_proficiency:
                    trait_proficiency = trait_proficiency.get(prof_type)
                    fuse(class_proficiency, trait_proficiency)
            self.proficiency = class_proficiency


# CHARACTER RACE GENERATOR
class _Traits:
    """DO NOT call class directly. Used to generate racial traits.
    Based on the inheriting class.

    Inherited by the following classes:

        - Aasimar
        - Dragonborn
        - Dwarf
        - Elf
        - Gnome
        - HalfElf
        - HalfOrc
        - Halfling
        - Human
        - Tiefling

    """

    def __init__(self, **kw) -> None:
        self.race = self.__class__.__name__
        """
            Args:
                kw:
                    - class_attr (dict)
                    - subrace (str)
                    - variant (bool)
        """

        if self.race == "_Traits":
            raise Exception("this class must be inherited")

        if "class_attr" not in kw and not isinstance(kw.get("class_attr"), dict):
            kw["class_attr"] = None
        if "subrace" not in kw:
            kw["subrace"] = None
        if "variant" not in kw or not isinstance(kw.get("variant"), bool):
            kw["variant"] = False

        self.class_attr = tuple(kw.get("class_attr").values())
        self.subrace = kw.get("subrace")
        self.variant = kw.get("variant")

        self.traits = reader("races", (self.race, "traits"))
        self.traits["skills"] = list()

        # Dragonborn character's get draconic ancestry.
        if self.race == "Dragonborn":
            draconic_ancestry = reader("races", (self.race, "traits", "ancestry"))
            draconic_ancestry = random.choice(draconic_ancestry)
            damage_resistance = None
            if draconic_ancestry in ("Black", "Copper",):
                damage_resistance = "Acid"
            elif draconic_ancestry in ("Blue", "Bronze",):
                damage_resistance = "Lightning"
            elif draconic_ancestry in ("Brass", "Gold", "Red",):
                damage_resistance = "Fire"
            elif draconic_ancestry == "Green":
                damage_resistance = "Poison"
            elif draconic_ancestry in ("Silver", "White"):
                damage_resistance = "Cold"

            breath_weapon = damage_resistance
            self.traits["ancestry"] = draconic_ancestry
            self.traits["breath"] = breath_weapon
            self.traits["resistance"] = [damage_resistance]

        # Dwarves get a random tool proficiency.
        if self.race == "Dwarf":
            tool_bonus = random.choice(self.traits.get("proficiency").get("tools"))
            self.traits["proficiency"]["tools"] = [tool_bonus]

        # Elves and HalfOrcs get a specific bonus skill.
        if self.race in ("Elf", "HalfOrc",):
            if self.race == "Elf":
                self.traits["skills"] = ["Perception"]
            elif self.race == "HalfOrc":
                self.traits["skills"] = ["Intimidation"]

        # Bonus languages for Half-Elf, Human or High Elf.
        if self.race in ("HalfElf", "Human") or self.subrace == "High":
            standard_languages = [
                "Common",
                "Dwarvish",
                "Elvish",
                "Giant",
                "Gnomish",
                "Goblin",
                "Halfling",
                "Orc",
            ]
            purge(standard_languages, self.traits.get("languages"))
            self.traits["languages"].append(random.choice(standard_languages))

        # Bonus skills for HalfElf and Human variants.
        if self.race == "Human" and self.variant or self.race == "HalfElf":
            all_skills = reader("races", (self.race, "traits", "skills"))
            if self.race == "HalfElf":
                self.traits["skills"] = random.sample(all_skills, 2)
            elif self.race == "Human":
                self.traits["skills"] = random.sample(all_skills, 1)

        # Human variants only have two bonus "racial" abilities.
        if self.race == "Human" and self.variant:
            if self.class_attr is not None:
                bonus_abilities = dict()
                for ability in self.class_attr:
                    bonus_abilities[ability] = 1
                self.traits["abilities"] = bonus_abilities

        if self.subrace is None:
            return
        else:
            subrace_traits = reader("subraces", (self.subrace, "traits"))
            self.traits = self._merge_traits(self.traits, subrace_traits)

    @staticmethod
    def _merge_traits(base_traits: dict, sub_traits: dict) -> dict:
        """Combines racial and subracial traits if applicable."""
        for trait, value in sub_traits.items():
            # No proficiency key index in base traits, add it.
            if trait not in base_traits:
                base_traits[trait] = {}

            if trait == "abilities":
                for ability, bonus in value.items():
                    base_traits[trait][ability] = bonus

            if trait == "cantrip":
                cantrip_list = reader("subraces", ("High", "traits", "cantrip"))
                bonus_cantrip = [random.choice(cantrip_list)]
                base_traits[trait] = bonus_cantrip

            if trait == "darkvision":
                if sub_traits.get(trait) > base_traits.get(trait):
                    base_traits[trait] = sub_traits.get(trait)

            if trait == "languages":
                for language in sub_traits.get(trait):
                    base_traits.get(trait).append(language)
                base_traits[trait].sort()

            if trait == "resistance":
                for element in value:
                    base_traits.get(trait).append(element)
                base_traits[trait].sort()

            if trait == "magic" or trait == "sensitivity" or trait == "toughness":
                base_traits[trait] = sub_traits.get(trait)

            if trait == "proficiency":
                for proficiency_type in list(sub_traits[trait].keys()):
                    if proficiency_type == "armors":
                        base_traits[trait].update(armors=sub_traits[trait]["armors"])

                    if proficiency_type == "tools":
                        base_traits[trait].update(tools=sub_traits[trait]["tools"])

                    if proficiency_type == "weapons":
                        base_traits[trait].update(weapons=sub_traits[trait]["weapons"])

            if trait == "tinker":
                base_traits[trait] = sub_traits.get(trait)
        return base_traits


class Aasimar(_Traits):
    def __init__(self, **kw) -> None:
        super(Aasimar, self).__init__(**kw)


class Dragonborn(_Traits):
    def __init__(self, **kw) -> None:
        super(Dragonborn, self).__init__(**kw)


class Dwarf(_Traits):
    def __init__(self, **kw) -> None:
        super(Dwarf, self).__init__(**kw)


class Elf(_Traits):
    def __init__(self, **kw) -> None:
        super(Elf, self).__init__(**kw)


class Gnome(_Traits):
    def __init__(self, **kw) -> None:
        super(Gnome, self).__init__(**kw)


class HalfElf(_Traits):
    def __init__(self, **kw) -> None:
        super(HalfElf, self).__init__(**kw)


class HalfOrc(_Traits):
    def __init__(self, **kw) -> None:
        super(HalfOrc, self).__init__(**kw)


class Halfling(_Traits):
    def __init__(self, **kw) -> None:
        super(Halfling, self).__init__(**kw)


class Human(_Traits):
    def __init__(self, **kw) -> None:
        super(Human, self).__init__(**kw)


class Tiefling(_Traits):
    def __init__(self, **kw) -> None:
        super(Tiefling, self).__init__(**kw)


def get_subraces_by_race(race: str) -> tuple:
    """Returns a list of subraces by race."""
    valid_subraces = list()
    for name, traits in reader("subraces").items():
        if traits.get("parent") == race:
            valid_subraces.append(name)
    return tuple(valid_subraces)


# CHARACTER SKILL GENERATOR
class SkillGenerator:
    """Generates skill set by background and klass."""

    def __init__(self, background: str, klass: str, bonus_racial_skills: list,) -> None:
        """
        Args:
            background (str): Character background.
            klass (str): Character's class.
            bonus_racial_skills (list): Character's skills.
        """
        skill_list = reader("skills")
        class_skills = list()
        for skill, attributes in skill_list.items():
            if klass in attributes.get("classes"):
                class_skills.append(skill)

        generated_skills = list()

        # Remove bonus racial skills from class skills.
        if len(bonus_racial_skills) is not 0:
            purge(class_skills, bonus_racial_skills)
            fuse(generated_skills, bonus_racial_skills)

        # Remove bonus background skills from class skills.
        background_skills = reader("backgrounds", (background, "skills"))
        if len(background_skills) is not 0:
            purge(class_skills, background_skills)
            fuse(generated_skills, background_skills)

        if klass in ("Rogue",):
            skill_allotment = 4
        elif klass in ("Bard", "Ranger"):
            skill_allotment = 3
        else:
            skill_allotment = 2
        fuse(generated_skills, random.sample(class_skills, skill_allotment))
        self.skills = generated_skills


def expand_skills(skills: list, score_array: OrderedDict) -> list:
    # Creates a detailed skill "list".
    exp_skill_list = list()
    for skill in skills:
        skill_ability = reader("skills", (skill, "ability"))
        ability_score = score_array.get(skill_ability).get("Value")
        skill_modifier = get_ability_modifier(ability_score)
        exp_skill_list.append((skill, skill_modifier))
    return exp_skill_list


def get_all_skills() -> list:
    return list(reader("skills").keys())


# LIST HELPER FUNCTIONS
def add(iterable: list, value: (bool, float, int, str), unique=False) -> list:
    """Adds a value into iterable.
    
    Args:
        iterable (list): Iterable to be added to.
        value (any): Value to add to iterable.
        unique (bool): Only unique values will be added if True.
    """
    if unique and value in iterable:
        return iterable

    iterable.append(value)
    iterable.sort()
    return iterable


def fuse(iterable: list, values: (list, tuple), unique=True) -> list:
    """Individual fuses values to iterable collection.

    Args:
        iterable (list): Iterable to be fused with.
        values (list, tuple): Values to be fused with iterable.
        unique (bool): Determines if only unique values with be fused.
    """
    if not isinstance(iterable, list):
        raise TypeError("argument 'iterable' must be of type 'list'.")

    if not isinstance(values, (list, tuple)):
        raise TypeError("argument 'values' must be of type 'list' or 'tuple'.")

    if len(values) is 0:
        return iterable

    for value in values:
        add(iterable, value, unique)

    iterable.sort()
    return iterable


def pick(iterable: list) -> (bool, dict, float, int, list, str, tuple):
    """Chooses random value from list then removes it.
    Args:
        iterable (list): Iterable to pick from.
    """
    if not isinstance(iterable, list):
        raise TypeError("argument 'iterable' must be of type 'list'.")

    if len(iterable) is 0:
        raise ValueError("cannot pick from an empty iterable.")

    selection = random.choice(iterable)
    iterable.remove(selection)
    return selection


def purge(iterable: list, values: (list, tuple)) -> list:
    """Individual purges values from iterable.
    
    Args:
        iterable (list): Iterable to remove values from.
        values (values): Collection of values to remove from iterable.
    """
    if not isinstance(iterable, list):
        raise TypeError("argument iterable must be of type 'list'.")

    if not isinstance(values, (list, tuple)):
        raise TypeError("argument 'values' must be of type 'list' or 'tuple'.")

    for value in values:
        if value in iterable:
            iterable.remove(value)
    return iterable
