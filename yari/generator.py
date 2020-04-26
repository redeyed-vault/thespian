from collections import OrderedDict
import math
import random

import numpy

from yari.reader import reader


# ATTRIBUTE GENERATOR
class _Bonuses:
    """Determines ability bonuses by race and subrace (if applicable)."""

    def __init__(self, race: str, variant: bool, primary: dict, subrace=None) -> None:
        """
        Args:
            race (str): Character's race.
            variant (bool): Use variant rules.
            primary (tuple): Character's primary abilities.
            subrace (str, None): Character's subrace (if applicable).
        """
        bonuses = dict()
        primary = list(primary.values())
        # Half-elf ability bonuses.
        if race == "HalfElf":
            ability_choices = [
                "Strength",
                "Dexterity",
                "Constitution",
                "Intelligence",
                "Wisdom",
            ]
            if "Charisma" in primary:
                primary.remove("Charisma")
                # Get the remaining primary ability, assign the bonus.
                saved_ability = pick(primary)
                bonuses[saved_ability] = 1
                # Remove the remaining ability from the choices.
                ability_choices.remove(saved_ability)
                # Choose third ability.
                bonuses[pick(ability_choices)] = 1
            else:
                for ability in primary:
                    bonuses[ability] = 1
        # Non-human or human non-variant ability bonuses.
        elif race == "Human" and not variant or race != "Human":
            racial_bonuses = reader("races", (race, "traits", "abilities"))
            for ability, bonus in racial_bonuses.items():
                bonuses[ability] = bonus
        # Human variant bonuses.
        elif race == "Human" and variant:
            racial_bonuses = primary
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

    def __init__(self, race: str, primary: dict, variant: bool, subrace=None) -> None:
        """
        Args:
            race (str): Character's race.
            primary (dict): Class primary abilities.
            variant (bool): Use variant rules.
            subrace (str, None): Character's subrace (if applicable).
        """
        super().__init__(race, variant, primary, subrace)

        # Ability score array structure.
        score_arr = OrderedDict()
        score_arr["Strength"] = None
        score_arr["Dexterity"] = None
        score_arr["Constitution"] = None
        score_arr["Intelligence"] = None
        score_arr["Wisdom"] = None
        score_arr["Charisma"] = None

        # Assign class specific primary abilities first.
        ability_choices = [
            "Strength",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
        ]

        generated_scores = list(self.roll_ability_scores(60))
        # Assign highest values to class specific abilities first.
        for ability in tuple(primary.values()):
            value = max(generated_scores)
            modifier = get_ability_modifier(value)
            score_arr[ability] = OrderedDict({"Value": value, "Modifier": modifier})
            ability_choices.remove(ability)
            generated_scores.remove(value)

        # Assign remaining abilities/scores.
        for _ in range(0, 4):
            ability = random.choice(ability_choices)
            value = random.choice(generated_scores)
            modifier = get_ability_modifier(value)
            score_arr[ability] = OrderedDict({"Value": value, "Modifier": modifier})
            ability_choices.remove(ability)
            generated_scores.remove(value)

        # Apply racial bonuses.
        for ability, bonus in self.bonuses.items():
            value = score_arr.get(ability).get("Value") + bonus
            modifier = get_ability_modifier(value)
            score_arr[ability] = OrderedDict({"Value": value, "Modifier": modifier})
        self.get = score_arr

    @staticmethod
    def roll_ability_scores(threshold: int) -> numpy.ndarray:
        """Generates six ability scores."""

        def roll() -> numpy.ndarray:
            """Returns random array between 1-6 x4."""
            return numpy.random.randint(low=1, high=6, size=4)

        results = numpy.array([], dtype=int)
        while results.sum() < threshold:
            for _ in range(1, 7):
                result = roll()
                excl_result = result.min(initial=None)
                ability_score = result.sum() - excl_result
                results = numpy.append(results, ability_score)
            score_total = results.sum()

            try:
                maximum_score = results.max(initial=None)
                minimum_score = results.min(initial=None)
            except ValueError:
                # FIX: Empty array bug, forces re-roll w/ bad values.
                maximum_score = 14
                minimum_score = 7

            if score_total < threshold or maximum_score < 15 or minimum_score < 8:
                results = numpy.array([], dtype=int)
        return results


def get_ability_modifier(score: int) -> int:
    """Returns ability modifier by score."""
    return score is not 0 and int((score - 10) / 2) or 0


def get_proficiency_bonus(level: int) -> int:
    """Returns a proficiency bonus value by level."""
    return math.ceil((level / 4) + 1)


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

    def __init__(self, archetype: (None, str), level: int) -> None:
        """
        Args:
            archetype (str, None): Character's archetype.
            level (int): Character's level.
        """
        self.class_ = self.__class__.__name__
        if self.class_ == "_Features":
            raise Exception("error: to use this class it must be inherited")

        if self.class_ not in tuple(reader("classes").keys()):
            raise ValueError("error: class '{}' does not exist".format(self.class_))

        valid_archetypes = get_paths_by_class(self.class_)
        if archetype not in valid_archetypes:
            archetype = random.choice(valid_archetypes)

        self.features = reader("classes", (self.class_,))

        self.features["abilities"] = self._enc_class_abilities(self.class_, archetype)
        self.features["archetype"] = archetype
        self.features["features"] = self._enc_class_features(
            self.features["features"], archetype, level
        )

        def roll(d: int, lv: int) -> numpy.ndarray:
            """Returns random array between low and d by lv."""
            return numpy.random.randint(low=1, high=d, size=lv)

        hit_die = self.features.get("hit_die")
        self.features["hit_die"] = f"{level}d{hit_die}"
        if level > 1:
            level = level - 1
        hp = roll(hit_die, level)

        if level > 1:
            self.features["hit_points"] = hp.sum() + hit_die
        else:
            self.features["hit_points"] = hit_die

        if has_class_spells(archetype):
            self.features["magic_class"] = self._enc_class_magic(archetype, level)

        prof = self._enc_class_proficiency(self.class_, archetype, level)
        self.features["proficiency"]["armors"] = prof["armors"]
        self.features["proficiency"]["tools"] = prof["tools"]
        self.features["proficiency"]["weapons"] = prof["weapons"]

        if (
            self.class_ == "Fighter"
            and archetype != "Eldritch Knight"
            or self.class_ == "Rogue"
            and archetype != "Arcane Trickster"
        ):
            self.features["spell_slots"] = ""
        else:
            self.features["spell_slots"] = self.features["spell_slots"].get(level)

        del self.features["paths"]

    @staticmethod
    def _enc_class_abilities(class_: str, archetype: str):
        a_list = reader("classes", (class_, "abilities",))
        if class_ == "Cleric":
            a_list[2] = random.choice(a_list[2])
        elif class_ in ("Fighter", "Ranger"):
            ability_choices = a_list.get(1)
            a_list[1] = random.choice(ability_choices)
            if class_ == "Fighter" and archetype != "Eldritch Knight":
                a_list[2] = "Constitution"
            elif class_ == "Fighter" and archetype == "Eldritch Knight":
                a_list[2] = "Intelligence"
            else:
                a_list[2] = a_list.get(2)
        elif class_ == "Rogue":
            if archetype != "Arcane Trickster":
                a_list[2] = "Charisma"
            else:
                a_list[2] = "Intelligence"
        elif class_ == "Wizard":
            ability_choices = a_list.get(2)
            a_list[2] = random.choice(ability_choices)
        return a_list

    @staticmethod
    def _enc_class_features(f_list: dict, archetype: str, level: int):
        c_features = dict()
        for lvl, feature in f_list.items():
            c_features[lvl] = feature
        f_list = c_features

        a_features = reader("paths", (archetype,))
        a_features = a_features.get("features")
        for lvl, feature in a_features.items():
            if lvl in f_list:
                for _feature in a_features.get(lvl):
                    f_list[lvl].append(_feature)
                f_list[lvl].sort()
            else:
                f_list[lvl] = list()
                for _feature in a_features.get(lvl):
                    f_list[lvl].append(_feature)
                f_list[lvl].sort()

        levels = list(f_list.keys())
        levels.sort()
        ff_list = dict()
        for _level in levels:
            if _level <= level:
                ff_list[_level] = f_list[_level]

        del a_features
        del f_list
        return ff_list

    @staticmethod
    def _enc_class_magic(archetype: str, level: int):
        c_magic = reader("paths", (archetype,))
        if "magic_cleric" in c_magic:
            c_magic = c_magic.get("magic_cleric")
        elif "magic_paladin" in c_magic:
            c_magic = c_magic.get("magic_paladin")

        if c_magic is not None:
            _c_magic = dict()
            for lvl, magic in c_magic.items():
                if lvl <= level:
                    _c_magic[lvl] = magic

            del c_magic
            return _c_magic

    @staticmethod
    def _enc_class_proficiency(class_: str, archetype: str, level: int):
        c_prof = reader("classes", (class_, "proficiency"))
        a_prof = reader("paths", (archetype, "proficiency"))
        for prof_type in ("armors", "tools", "weapons"):
            if prof_type == "tools":
                if archetype == "Assassin" and level < 3:
                    continue
                elif class_ == "Monk":
                    monk_bonus_tool = random.choice(c_prof[prof_type])
                    c_prof[prof_type] = list()
                    c_prof[prof_type].append(monk_bonus_tool)
            elif (
                prof_type == "weapons" and archetype == "College of Valor" and level < 3
            ):
                continue
            else:
                p_list = a_prof[prof_type]
                if len(p_list) is not 0:
                    for prof in p_list:
                        c_prof[prof_type].append(prof)
                    c_prof[prof_type].sort()
        return c_prof


class Barbarian(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Bard(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Cleric(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Druid(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Fighter(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Monk(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Paladin(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Ranger(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Rogue(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Sorcerer(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Warlock(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


class Wizard(_Features):
    def __init__(self, level, archetype=None) -> None:
        super().__init__(archetype, level)


def get_paths_by_class(class_: str) -> tuple:
    return tuple(reader("classes", (class_, "paths")))


def has_class_spells(archetype: str) -> bool:
    spell_list = reader("paths", (archetype,))
    if "magic_cleric" in spell_list:
        return "magic_cleric" in spell_list
    elif "magic_paladin" in spell_list:
        return "magic_paladin" in spell_list


# CHARACTER IMPROVEMENT GENERATOR
class ImprovementGenerator:
    """Determines/applies feats and ability upgrades (if applicable)."""

    def __init__(
        self,
        race: str,
        class_: str,
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
        variant: bool,
    ) -> None:
        """
        Args:
            race (str): Character's race.
            class_ (str): Character's class.
            level (int): Character's level.
            primary_ability (dict): Primary abilities for class_.
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
        self.class_ = class_
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
        if class_ == "Druid":
            self.languages.append("Druidic")

        if class_ == "Rogue":
            self.languages.append("Thieves' cant")

        # Determine number of applicable upgrades
        upgrades = 0
        for _ in range(1, level + 1):
            if (_ % 4) == 0 and _ is not 20:
                upgrades += 1

        if class_ == "Fighter" and level >= 6:
            upgrades += 1

        if class_ == "Rogue" and level >= 8:
            upgrades += 1

        if class_ == "Fighter" and level >= 14:
            upgrades += 1

        if level >= 19:
            upgrades += 1

        # Cycle through the available upgrades (if applicable)
        if upgrades is 0:
            return

        primary_ability = list(primary_ability.values())
        for _ in range(1, upgrades):
            if len(primary_ability) is 0:
                upgrade_option = "Feat"
            else:
                upgrade_option = random.choice(["Ability", "Feat"])

            if upgrade_option == "Ability":
                try:
                    if len(primary_ability) is 2:
                        if self.isadjustable(primary_ability):
                            for ability in primary_ability:
                                self.set_score_array(ability, 1)
                                if not self.isadjustable(ability):
                                    primary_ability.remove(ability)
                        elif len(primary_ability) is 1:
                            ability = primary_ability[0]
                            if self.isadjustable(ability):
                                self.set_score_array(ability, 2)
                                if not self.isadjustable(ability):
                                    primary_ability.remove(ability)
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
            if self.class_ in ("Cleric", "Druid"):
                self.set_score_array("Wisdom", 1)
            elif self.class_ in ("Wizard",):
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
            and self.class_ == "Monk"
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
                if feat == "Magic Initiative" and self.class_ not in (
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
                    if self.class_ in ("Cleric", "Druid"):
                        my_score = self.score_array["Wisdom"]["Value"]
                        required_score = prq.get("abilities").get("Wisdom")
                    elif self.class_ == "Wizard":
                        my_score = self.score_array["Intelligence"]["Value"]
                        required_score = prq.get("abilities").get("Intelligence")

                    if my_score < required_score:
                        return False
        return True

    def isadjustable(self, abilities: (list, str)) -> (bool, int):
        """Determines if an ability can be adjusted i.e: not over 20"""
        if isinstance(abilities, (list)):
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
                    class_proficiency = fuse(class_proficiency, trait_proficiency)
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

    def __init__(self, subrace: (None, str)) -> None:
        self.race = self.__class__.__name__
        try:
            if self.race == "_Traits":
                raise Exception("error: to use this class it must be inherited")

            if self.race not in tuple(reader("races").keys()):
                raise ValueError(f"error: race '{self.race}' does not exist")
        except (Exception, ValueError) as error:
            exit(error)
        else:
            self.traits = reader("races", (self.race, "traits"))

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
        # Humans and Half-elves get a bonus language
        if self.race == "HalfElf" or self.race == "Human":
            purge(standard_languages, self.traits.get("languages"))
            self.traits["languages"].append(random.choice(standard_languages))

        if subrace is None:
            pass
        else:
            self.valid_subraces = get_subraces_by_race(self.race)
            try:
                if subrace not in self.valid_subraces:
                    raise ValueError(f"error: invalid subrace '{subrace}'")
            except ValueError as error:
                exit(error)
            else:
                subrace_traits = reader("subraces", (subrace, "traits"))

                # High elves get a random bonus language
                if subrace == "High":
                    purge(standard_languages, self.traits.get("languages"))
                    self.traits["languages"].append(random.choice(standard_languages))

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
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class Dragonborn(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class Dwarf(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class Elf(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class Gnome(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class HalfElf(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class HalfOrc(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class Halfling(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class Human(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


class Tiefling(_Traits):
    def __init__(self, subrace=None) -> None:
        super().__init__(subrace)


def get_subraces_by_race(race: str) -> tuple:
    """Returns a list of subraces by race."""
    valid_subraces = list()
    for name, traits in reader("subraces").items():
        if traits.get("parent") == race:
            valid_subraces.append(name)
    return tuple(valid_subraces)


# CHARACTER SKILL GENERATOR
class SkillGenerator:
    """Generates skill set by race, background, class_, level and variant."""

    def __init__(
        self,
        race: str,
        background: str,
        class_: str,
        archetype: str,
        level: int,
        variant: bool,
    ) -> None:
        """
        Args:
            race (str): Character's race.
            background (str): Character background.
            class_ (str): Character's class.
            archetype (str): Character's archetype.
            level (int): Character's level.
            variant (bool): Use variant rules.
        """
        self.level = level
        generated_skill_list = list()
        # Organize skills by class.
        class_skills = self.get_skills_by_class(class_)

        # Remove background skills from class skills.
        background_skills = reader("backgrounds", (background, "skills"))
        purge(class_skills, background_skills)

        # Add racial skills first.
        if race in ("Elf", "Half-orc"):
            if race == "Half-orc":
                racial_skill = "Intimidation"
            else:
                racial_skill = "Perception"
            # If racial skill is class skill, remove it.
            if racial_skill in class_skills:
                class_skills.remove(racial_skill)
            generated_skill_list.append(racial_skill)
        elif race == "Half-elf" or race == "Human":
            # Remove background, class and racial skills from skill choices.
            all_skill_choices = list(reader("skills").keys())
            purge(all_skill_choices, background_skills)
            purge(all_skill_choices, class_skills)
            if race == "Half-elf":
                fuse(generated_skill_list, random.sample(all_skill_choices, 2))
            elif race == "Human" and variant:
                generated_skill_list.append(random.choice(all_skill_choices))

        # Next, add background skills.
        if len(background_skills) is not 0:
            fuse(generated_skill_list, background_skills)

        # Finally, choose class skills.
        if class_ in ("Rogue",):
            skill_allotment = 4
        elif class_ in ("Bard", "Ranger"):
            skill_allotment = 3
        else:
            skill_allotment = 2
        fuse(generated_skill_list, random.sample(class_skills, skill_allotment))

        if archetype == "College of Lore" and level >= 3:
            all_skill_choices = list(reader("skills").keys())
            all_skill_choices = purge(all_skill_choices, generated_skill_list)
            fuse(generated_skill_list, random.sample(all_skill_choices, 3))
        self.skills = generated_skill_list

    def expand_skill_list(self, skills: list, abilities: (dict, OrderedDict)) -> list:
        # Creates a detailed skill "list".
        expanded_skill_list = list()
        for skill in skills:
            skill_ability = reader("skills", (skill, "ability"))
            ability_score = abilities.get(skill_ability).get("Value")
            skill_value = get_proficiency_bonus(self.level) + get_ability_modifier(
                ability_score
            )
            expanded_skill_list.append((skill, skill_ability, skill_value))
        return expanded_skill_list

    @staticmethod
    def get_skills_by_class(class_: str) -> list:
        """Gets skills list by class_."""
        class_skills = list()
        if class_ != "Bard":
            for skill, attributes in reader("skills").items():
                if class_ in attributes.get("classes"):
                    class_skills.append(skill)
        else:
            skill_list = list(reader("skills").keys())
            class_skills = random.sample(skill_list, 3)
        return class_skills


def add(
    iterable: list, value: (bool, dict, float, int, list, str, tuple), unique=False
) -> (list, bool):
    """Adds a value into iterable.
    
    Args:
        iterable (list): Iterable to be added to.
        value (any): Value to add to iterable.
        unique (bool): Only unique values will be added if True.
    """
    if unique and value in iterable:
        return False
    iterable.append(value)
    iterable.sort()
    return iterable


def fuse(iterable: list, values: (list, tuple), unique=False) -> list:
    """Individual fuses values to iterable collection.

    Args:
        iterable (list): Iterable to be fused with.
        values (list, tuple): Values to be fused with iterable.
    """
    try:
        if not isinstance(iterable, list):
            raise TypeError("argument 'iterable' must be of type 'list'.")
        if not isinstance(values, (list, tuple)):
            raise TypeError("argument 'values' must be of type 'list' or 'tuple'.")
        if len(values) is 0:
            raise ValueError
    except TypeError as e:
        exit(e)
    except ValueError:
        exit("cannot fuse from an empty iterable.")
    for value in values:
        add(iterable, value)
    return iterable


def pick(iterable: list) -> (bool, dict, float, int, list, str, tuple):
    """Chooses random value from list then removes it.
    Args:
        iterable (list): Iterable to pick from.
    """
    try:
        if not isinstance(iterable, list):
            raise TypeError
        if len(iterable) is 0:
            raise ValueError
    except TypeError:
        exit("argument 'iterable' must be of type 'list'.")
    except ValueError:
        exit("cannot pick from an empty iterable.")
    selection = random.choice(iterable)
    iterable.remove(selection)
    return selection


def purge(iterable: list, values: (list, tuple)) -> list:
    """Individual purges values from iterable.
    
    Args:
        iterable (list): Iterable to remove values from.
        values (values): Collection of values to remove from iterable.
    """
    try:
        if not isinstance(iterable, list):
            raise TypeError("argument iterable must be of type 'list'.")
        if not isinstance(values, (list, tuple)):
            raise TypeError(
                "argument 'values' must be of type 'list' or 'tuple'."
            )
    except TypeError as error:
        exit(error)
    for value in values:
        if value in iterable:
            iterable.remove(value)
    return iterable
