import math
import random

from yari.exceptions import InheritanceError, InvalidValueError
from yari.loader import _read
from yari.skills import get_all_skills


class _Classes:
    """DO NOT call class directly. Used to generate class features.

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

    def __init__(self, path: str, level: int) -> None:
        """
        Args:
            path (str): Character's chosen path.
            level (int): Character's chosen level.

        """
        self.klass = self.__class__.__name__
        if self.klass == "_Classes":
            raise InheritanceError("This class must be inherited")

        if not get_is_class(self.klass):
            raise InvalidValueError(f"Character class '{self.klass}' is invalid")

        if path is not None and not get_is_path(path, self.klass):
            raise InvalidValueError(f"Character archetype '{path}' is invalid")
        else:
            self.path = path

        if not isinstance(level, int):
            raise InvalidValueError("Argument level value must be of type 'int'")
        elif level not in range(1, 21):
            raise InvalidValueError("Argument level value must be between 1-20")
        else:
            self.level = level

        self.all = _read(self.klass, file="classes")

        del self.all["paths"]

        self._add_class_abilities()
        self._add_class_features()
        self._add_class_hit_die()
        self._add_class_path_magic()
        self._add_class_proficiency("Armor")
        self._add_class_proficiency("Tools")
        self._add_class_proficiency("Weapons")
        self._add_class_spell_slots()

        self.primary_ability = self.all.get("abilities")
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
        return '<{} path="{}" level="{}">'.format(self.klass, self.path, self.level)

    def _add_class_abilities(self):
        """Generates primary abilities by character class.

            Classes with multiple primary ability choices will select one.

                - Fighter: Strength|Dexterity
                - Fighter: Constitution|Intelligence
                - Ranger: Dexterity|Strength
                - Rogue: Charisma|Intelligence
                - Wizard: Constitution|Dexterity

        """
        class_abilities = _read(self.klass, "abilities", file="classes")
        if self.klass == "Cleric":
            class_abilities[2] = random.choice(class_abilities[2])
        elif self.klass in ("Fighter", "Ranger"):
            ability_choices = class_abilities.get(1)
            class_abilities[1] = random.choice(ability_choices)
            if self.klass == "Fighter" and self.path != "Eldritch Knight":
                class_abilities[2] = "Constitution"
            elif self.klass == "Fighter" and self.path == "Eldritch Knight":
                class_abilities[2] = "Intelligence"
            else:
                class_abilities[2] = class_abilities.get(2)
        elif self.klass == "Rogue":
            if self.path != "Arcane Trickster":
                class_abilities[2] = "Charisma"
            else:
                class_abilities[2] = "Intelligence"
        elif self.klass == "Wizard":
            ability_choices = class_abilities.get(2)
            class_abilities[2] = random.choice(ability_choices)

        self.all["abilities"] = class_abilities

    def _add_class_features(self):
        """Generates a dictionary of features by class, path & level."""
        try:
            class_features = _read(self.klass, "features", file="classes")
            path_features = _read(self.path, "features", file="paths")

            final_feature_list = dict()
            for level in range(1, self.level + 1):
                level_features = list()
                if level in class_features:
                    level_features = level_features + class_features[level]
                if level in path_features:
                    level_features = level_features + path_features[level]
                if len(level_features) is not 0:
                    level_features.sort()
                    final_feature_list[level] = tuple(level_features)

            self.all["features"] = final_feature_list
        except AttributeError:
            print(
                f"Character class '{self.klass}' or the archetype '{self.path}' is invalid."
            )

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

    def _add_class_path_magic(self):
        """Builds a dictionary list of specialized magic spells."""
        self.all["magic"] = dict()

        if not has_class_spells(self.path):
            return

        magic = dict()
        class_magic = _read(self.path, "magic", file="paths")

        if len(class_magic) is not 0:
            for level, spells in class_magic.items():
                if level <= self.level:
                    magic[level] = tuple(spells)

            del class_magic
            self.all["magic"] = magic
        else:
            self.all["magic"] = dict()

    def _add_class_proficiency(self, category: str):
        """Generates character's proficiencies by category."""
        path_proficiency = _read(self.path, file="paths")

        # Skill handling and allotment.
        skills = self.all["proficiency"][4]
        if self.klass in ("Rogue",):
            skill_allotment = 4
        elif self.klass in ("Bard", "Ranger"):
            skill_allotment = 3
        else:
            skill_allotment = 2

        if self.path == "Assassin":
            assassin_skills = path_proficiency.get("proficiency")[0][1]
            skills = [x for x in skills[1] if x not in assassin_skills]
            skills = random.sample(skills, skill_allotment)
            if self.level >= 3:
                skills = skills + assassin_skills
            self.all["proficiency"][4] = ["Skills", skills]
        elif self.path == "College of Lore":
            skills = random.sample(skills[1], skill_allotment)
            self.all["proficiency"][4] = ["Skills", skills]
            if self.level >= 3:
                my_skills = self.all["proficiency"][4][1]
                lore_skills = [x for x in get_all_skills() if x not in my_skills]
                skills = skills + random.sample(lore_skills, 3)
                self.all["proficiency"][4] = ["Skills", skills]
        else:
            skills = random.sample(skills[1], skill_allotment)
            self.all["proficiency"][4] = ["Skills", skills]
        self.all["proficiency"][4][1].sort()

        # Proficiency handling and allotment (if applicable).
        self.all["proficiency_bonus"] = get_proficiency_bonus(self.level)

        if "proficiency" not in path_proficiency:
            return

        class_proficiency = self.all.get("proficiency")
        path_proficiency = path_proficiency.get("proficiency")
        class_extract = [cp for cp in class_proficiency if cp[0] == category]
        path_extract = [pp for pp in path_proficiency if pp[0] == category]
        for index, proficient in enumerate(class_proficiency):
            if proficient[0] == category:
                try:
                    revised_proficiency = class_extract[0][1] + path_extract[0][1]
                    revised_proficiency.sort()
                    self.all["proficiency"][index] = [category, revised_proficiency]
                except IndexError:
                    pass

        self.all["proficiency"] = [tuple(x) for x in self.all.get("proficiency")]

    def _add_class_spell_slots(self):
        """Generates character's spell slots."""
        if (
            self.klass == "Fighter"
            and self.path != "Eldritch Knight"
            or self.klass == "Rogue"
            and self.path != "Arcane Trickster"
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
    def __init__(self, path, level) -> None:
        super(Barbarian, self).__init__(path, level)


class Bard(_Classes):
    def __init__(self, path, level) -> None:
        super(Bard, self).__init__(path, level)


class Cleric(_Classes):
    def __init__(self, path, level) -> None:
        super(Cleric, self).__init__(path, level)


class Druid(_Classes):
    def __init__(self, path, level) -> None:
        super(Druid, self).__init__(path, level)


class Fighter(_Classes):
    def __init__(self, path, level) -> None:
        super(Fighter, self).__init__(path, level)


class Monk(_Classes):
    def __init__(self, path, level) -> None:
        super(Monk, self).__init__(path, level)


class Paladin(_Classes):
    def __init__(self, path, level) -> None:
        super(Paladin, self).__init__(path, level)


class Ranger(_Classes):
    def __init__(self, path, level) -> None:
        super(Ranger, self).__init__(path, level)


class Rogue(_Classes):
    def __init__(self, path, level) -> None:
        super(Rogue, self).__init__(path, level)


class Sorcerer(_Classes):
    def __init__(self, path, level) -> None:
        super(Sorcerer, self).__init__(path, level)


class Warlock(_Classes):
    def __init__(self, path, level) -> None:
        super(Warlock, self).__init__(path, level)


class Wizard(_Classes):
    def __init__(self, path, level) -> None:
        super(Wizard, self).__init__(path, level)


def get_is_class(klass: str) -> bool:
    """Returns whether klass is valid."""
    return klass in _read(file="classes")


def get_is_path(path: str, klass: str) -> bool:
    """Returns whether path is a valid path of klass."""
    return path in _read(klass, "paths", file="classes")


def get_paths_by_class(klass) -> tuple:
    """Returns a tuple of valid paths for klass."""
    return _read(klass, "paths", file="classes")


def get_proficiency_bonus(level: int) -> int:
    """Returns a proficiency bonus value by level."""
    return math.ceil((level / 4) + 1)


def has_class_spells(path: str) -> bool:
    """Returns whether class path has spells."""
    try:
        class_spells = _read(path, "magic", file="paths")
        return len(class_spells) is not 0
    except TypeError:
        return False
