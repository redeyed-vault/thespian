import math
import random

from yari.loader import load, QueryNotFound


ALLOWED_PC_BACKGROUNDS = load(file="classes")
ALLOWED_PC_CLASSES = load(file="classes")
ALLOWED_PC_SUBCLASSES = load(file="subclasses")


class _Classes:
    """
    DO NOT call class directly. Used to generate class features.

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

    :param str subclass: Character's chosen subclass.
    :param str background: Character's chosen background.
    :param int level: Character's chosen level.
    :param list race_skills: Character's bonus racial skills (if applicable).

    """

    def __init__(
        self, subclass: str, background: str, level: int, race_skills: list
    ) -> None:
        self.klass = self.__class__.__name__
        if self.klass == "_Classes":
            raise Exception(
                "This class must be inherited to use. It is currently used by "
                "the Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, "
                "Ranger, Rogue, Sorcerer, Warlock and Wizard 'job' classes."
            )

        if not get_is_class(self.klass):
            raise ValueError(f"Character class '{self.klass}' is invalid.")

        if not isinstance(level, int):
            raise ValueError("Argument 'level' value must be of type 'int'.")
        elif level not in range(1, 21):
            raise ValueError("Argument 'level' value must be between 1-20.")
        else:
            self.level = level

        if self.level >= 3:
            if get_is_subclass(subclass, self.klass):
                self.subclass = subclass
            else:
                raise ValueError(
                    f"Character class '{self.klass}' has no subclass '{subclass}'."
                )
        else:
            self.subclass = ""

        if get_is_background(background):
            self.background = background
        else:
            raise ValueError(f"Character background '{background}' is invalid.")

        if not isinstance(race_skills, list):
            raise ValueError("Argument 'race_skills' value must be a 'list'.")
        else:
            self.race_skills = race_skills

        self.all = load(self.klass, file="classes")

        self._add_class_abilities()
        self._add_class_equipment()
        self._add_class_features()
        self._add_class_hit_die()
        self._add_class_subclass_magic()
        self._add_class_proficiencies()
        self._add_class_skills()
        self._add_class_spell_slots()

        self.primary_ability = self.all.get("abilities")
        self.subclasses = self.all.get("subclasses")
        self.default_background = self.all.get("background")
        self.features = self.all.get("features")
        self.hit_die = self.all.get("hit_die")
        self.hit_points = self.all.get("hit_points")
        self.proficiency_bonus = self.all.get("proficiency_bonus")
        self.armors = self.all.get("proficiency")[0][1]
        self.tools = self.all.get("proficiency")[1][1]
        self.weapons = self.all.get("proficiency")[2][1]
        self.saving_throws = self.all.get("proficiency")[3][1]
        self.skills = self.all.get("proficiency")[4][1]
        self.magic = self.all["magic"]
        self.spell_slots = self.all.get("spell_slots")

    def __repr__(self):
        if self.subclass != "":
            return '<{} subclass="{}" level="{}">'.format(
                self.klass, self.subclass, self.level
            )
        else:
            return '<{} level="{}">'.format(self.klass, self.level)

    def _add_class_abilities(self):
        """
        Generates primary abilities by character class.

        Classes with multiple primary ability choices will select one.

            - Fighter: Strength|Dexterity
            - Fighter: Constitution|Intelligence
            - Ranger: Dexterity|Strength
            - Rogue: Charisma|Intelligence
            - Wizard: Constitution|Dexterity

        """
        class_abilities = load(self.klass, "abilities", file="classes")
        if self.klass == "Cleric":
            class_abilities[2] = random.choice(class_abilities[2])
        elif self.klass in ("Fighter", "Ranger"):
            ability_choices = class_abilities.get(1)
            class_abilities[1] = random.choice(ability_choices)
            if self.klass == "Fighter" and self.subclass != "Eldritch Knight":
                class_abilities[2] = "Constitution"
            elif self.klass == "Fighter" and self.subclass == "Eldritch Knight":
                class_abilities[2] = "Intelligence"
            else:
                class_abilities[2] = class_abilities.get(2)
        elif self.klass == "Rogue":
            if self.subclass != "Arcane Trickster":
                class_abilities[2] = "Charisma"
            else:
                class_abilities[2] = "Intelligence"
        elif self.klass == "Wizard":
            ability_choices = class_abilities.get(2)
            class_abilities[2] = random.choice(ability_choices)

        self.all["abilities"] = class_abilities

    def _add_class_equipment(self):
        """Generates a list of starting equipment by class & background."""
        class_equipment = load(self.klass, "equipment", file="classes")
        background_equipment = load(self.background, "equipment", file="backgrounds")
        equipment = class_equipment + background_equipment
        equipment.sort()
        self.all["equipment"] = self.equipment = equipment

    def _add_class_features(self):
        """Generates a dictionary of features by class, subclass & level."""

        def merge(cls_features: dict, sc_features: dict) -> dict:
            for lv, ft in sc_features.items():
                if lv in cls_features:
                    feature_list = cls_features[lv] + sc_features[lv]
                    feature_list.sort()
                    cls_features[lv] = feature_list
                else:
                    cls_features[lv] = sc_features[lv]
            return cls_features

        try:
            class_features = load(self.klass, "features", file="classes")
            if self.subclass != "":
                subclass_features = load(self.subclass, "features", file="subclasses")
                features = merge(class_features, subclass_features)
            else:
                features = class_features
            # Create feature dictionary based on level.
            features = {lv: features[lv] for lv in features if lv <= self.level}
        except (TypeError, KeyError) as e:
            # exit("Cannot find class/subclass '{}'")
            exit(e)
        else:
            for lv, fts in features.items():
                features[lv] = tuple(fts)
            self.all["features"] = features

    def _add_class_hit_die(self):
        """Generates hit die and point totals."""
        hit_die = self.all.get("hit_die")
        self.all["hit_die"] = f"{self.level}d{hit_die}"
        self.all["hit_points"] = hit_die
        if self.level > 1:
            new_level = self.level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            self.all["hit_points"] += sum(die_rolls)

    def _add_class_subclass_magic(self):
        """Builds a dictionary list of specialized magic spells."""
        self.all["magic"] = dict()

        if self.subclass == "":
            return

        if not has_class_spells(self.subclass):
            return

        magic = dict()
        class_magic = load(self.subclass, "magic", file="subclasses")

        if len(class_magic) != 0:
            for level, spells in class_magic.items():
                if level <= self.level:
                    magic[level] = tuple(spells)

            del class_magic
            self.all["magic"] = magic
        else:
            self.all["magic"] = dict()

    def _add_class_proficiencies(self):
        """Merge class proficiencies with subclass proficiencies (if applicable)."""
        if self.subclass == "":
            return

        for category in ("Armor", "Tools", "Weapons"):
            for index, proficiency in enumerate(self.all.get("proficiency")):
                if category in proficiency:
                    if (
                        category
                        in (
                            "Armor",
                            "Weapons",
                        )
                        and self.subclass == "College of Valor"
                        or self.subclass == "College of Swords"
                        and self.level < 3
                    ):
                        return
                    elif (
                        category == "Tools"
                        and self.subclass == "Assassin"
                        and self.level < 3
                    ):
                        return

                    try:
                        subclass_proficiency = [
                            x for x in get_subclass_proficiency(self.subclass, category)
                        ]
                        proficiencies = proficiency[1] + subclass_proficiency[0]
                        self.all["proficiency"][index] = [category, proficiencies]
                    except IndexError:
                        pass

        # Monk bonus tool or musical instrument proficiency.
        if self.klass == "Monk":
            tool_selection = [random.choice(self.all["proficiency"][1][1])]
            self.all["proficiency"][1][1] = tool_selection

        self.all["proficiency"] = [tuple(x) for x in self.all.get("proficiency")]

    def _add_class_skills(self):
        """Generates character's skill set."""
        # Skill handling and allotment.
        skill_pool = self.all["proficiency"][4][1]
        skills = list()

        # Get skill allotment by class.
        if self.klass in ("Rogue",):
            allotment = 4
        elif self.klass in ("Bard", "Ranger"):
            allotment = 3
        else:
            allotment = 2

        # Remove any bonus racial skill from pool.
        if len(self.race_skills) != 0:
            skill_pool = [x for x in skill_pool if x not in self.race_skills]
            skills = skills + self.race_skills

        skills = skills + random.sample(skill_pool, allotment)

        if self.subclass == "College of Lore" and self.level >= 3:
            lore_skills = [x for x in get_all_skills() if x not in skills]
            skills = skills + random.sample(lore_skills, 3)

        skills.sort()
        self.all["proficiency"][4] = ["Skills", skills]

        # Proficiency handling and allotment (if applicable).
        self.all["proficiency_bonus"] = get_proficiency_bonus(self.level)

    def _add_class_spell_slots(self):
        """Generates character's spell slots (if ANY)."""
        if (
            self.klass == "Fighter"
            and self.subclass != "Eldritch Knight"
            or self.klass == "Rogue"
            and self.subclass != "Arcane Trickster"
        ):
            self.all["spell_slots"] = "0"
        else:
            spell_slots = self.all.get("spell_slots")
            if self.level not in spell_slots:
                spell_slots = "0"
            else:
                spell_slots = spell_slots.get(self.level)
            self.all["spell_slots"] = spell_slots


class Barbarian(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Barbarian, self).__init__(subclass, background, level, race_skills)


class Bard(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Bard, self).__init__(subclass, background, level, race_skills)


class Cleric(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Cleric, self).__init__(subclass, background, level, race_skills)


class Druid(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Druid, self).__init__(subclass, background, level, race_skills)


class Fighter(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Fighter, self).__init__(subclass, background, level, race_skills)


class Monk(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Monk, self).__init__(subclass, background, level, race_skills)


class Paladin(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Paladin, self).__init__(subclass, background, level, race_skills)


class Ranger(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Ranger, self).__init__(subclass, background, level, race_skills)


class Rogue(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Rogue, self).__init__(subclass, background, level, race_skills)


class Sorcerer(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Sorcerer, self).__init__(subclass, background, level, race_skills)


class Warlock(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Warlock, self).__init__(subclass, background, level, race_skills)


class Wizard(_Classes):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Wizard, self).__init__(subclass, background, level, race_skills)


def get_default_background(klass: str):
    """
    Returns the default background by klass.

    :param str klass: Characters chosen class.

    """
    return load(klass, "background", file="classes")


def get_is_background(background: str) -> bool:
    """
    Returns whether the background is valid.

    :param str background: Chosen background to check.

    """
    return background in load(file="backgrounds")


def get_is_class(klass: str) -> bool:
    """
    Returns whether the klass is valid.

    :param str klass: Character's chosen class.

    """
    return klass in load(file="classes")


def get_is_subclass(subclass: str, klass: str) -> bool:
    """
    Returns whether subclass is a valid subclass of klass.

    :param str subclass: Character's chosen subclass.
    :param str klass: Character's chosen class.

    """
    return subclass in load(klass, "subclasses", file="classes")


def get_subclass_proficiency(subclass: str, category: str):
    """
    Returns subclass bonus proficiencies (if ANY).

    :param str subclass: Character subclass to get proficiencies for.
    :param str category: Proficiency category to get proficiencies for.

    """
    if category not in ("Armor", "Tools", "Weapons"):
        raise ValueError("Argument 'category' must be 'Armor', 'Tools' or 'Weapons'.")
    else:
        feature_list = load(subclass, file="subclasses")
        if "proficiency" in feature_list:
            proficiencies = feature_list.get("proficiency")
            for proficiency in proficiencies:
                if proficiency[0] == category:
                    yield proficiency[1]


def get_all_skills() -> list:
    """Returns a list of ALL skills."""
    return load(file="skills")


def get_background_skills(background: str):
    """
    Returns bonus skills by background (if applicable).

    :param str background: Background to return background skills for.

    """
    return load(background, "skills", file="backgrounds")


def get_subclasses_by_class(klass: str) -> tuple:
    """
    Returns a tuple of valid subclasses for klass.

    :param str klass: Character's class.

    """
    return load(klass, "subclasses", file="classes")


def get_proficiency_bonus(level: int) -> int:
    """
    Returns a proficiency bonus value by level.

    :param int level: Level of character.

    """
    return math.ceil((level / 4) + 1)


def has_class_spells(subclass: str) -> bool:
    """
    Returns whether class subclass has spells.

    :param str subclass: Character's subclass.

    """
    try:
        class_spells = load(subclass, "magic", file="subclasses")
        return len(class_spells) != 0
    except (TypeError, QueryNotFound):
        return False
