import math
import random

from yari.collect import fuse
from yari.exceptions import InheritanceError, InvalidValueError
from yari.reader import reader


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
            raise InheritanceError("this class must be inherited")

        if not get_is_class(self.klass):
            raise InvalidValueError(f"class '{self.klass}' does not exist")

        if path is not None and not get_is_path(path, self.klass):
            raise InvalidValueError(f"class path {path} is invalid")
        else:
            self.path = path

        if not isinstance(level, int):
            raise InvalidValueError("level value must be of type 'int'")
        elif level not in range(1, 21):
            raise InvalidValueError("level value must be between 1-20")
        else:
            self.level = level

        self.features = reader("classes", (self.klass,))
        self.features["abilities"] = self._get_class_abilities()
        self.features["features"] = self._get_class_features()
        self.features["path"] = self.path
        if (
            self.klass == "Fighter"
            and self.path != "Eldritch Knight"
            or self.klass == "Rogue"
            and self.path != "Arcane Trickster"
        ):
            self.features["spell_slots"] = "0"
        else:
            spell_slots = self.features.get("spell_slots")
            if self.level not in spell_slots:
                spell_slots = "0"
            else:
                spell_slots = spell_slots.get(self.level)
            self.features["spell_slots"] = spell_slots

        if has_class_spells(self.path):
            self._get_class_path_magic()

        self._get_class_hit_die()
        self._get_class_proficiency("armors")
        self._get_class_proficiency("tools")
        self._get_class_proficiency("weapons")

        del self.features["paths"]

    def __repr__(self):
        return "<{}, {}>".format(self.klass, self.path)

    def _get_class_abilities(self):
        """Gets primary class abilities.
            Classes with multiple primary ability choices will select one.

            - Fighter: Strength|Dexterity
            - Fighter: Constitution|Intelligence
            - Ranger: Dexterity|Strength
            - Rogue: Charisma|Intelligence
            - Wizard: Constitution|Dexterity

        """
        class_abilities = reader("classes", (self.klass,)).get("abilities")
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
        return class_abilities

    def _get_class_features(self):
        """Builds a dictionary of features by class, path & level."""
        try:
            feature_list = reader("classes", (self.klass,)).get("features")
            path_feature_list = reader("paths", (self.path,)).get("features")

            final_feature_list = dict()
            for level in range(1, self.level + 1):
                feature_row = list()
                if level in feature_list:
                    fuse(feature_row, feature_list[level])
                if level in path_feature_list:
                    fuse(feature_row, path_feature_list[level])
                if len(feature_row) is not 0:
                    final_feature_list[level] = feature_row

            return final_feature_list
        except AttributeError:
            print(self.path)

    def _get_class_hit_die(self):
        """Generates hit die and point totals."""
        hit_die = self.features.get("hit_die")
        self.features["hit_die"] = f"{self.level}d{hit_die}"
        self.features["hit_points"] = hit_die
        if self.level > 1:
            new_level = self.level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            self.features["hit_points"] += sum(die_rolls)

    def _get_class_path_magic(self):
        """Builds a dictionary list of specialized magic spells."""
        magic = dict()
        class_magic = reader("paths", (self.path,)).get("magic")

        if len(class_magic) is not 0:
            for level, spells in class_magic.items():
                if level <= self.level:
                    magic[level] = spells

            del class_magic
            self.features["magic"] = magic
        else:
            self.features["magic"] = dict()

    def _get_class_proficiency(self, prof_type: str):
        class_proficiency = reader("classes", (self.klass,)).get("proficiency")
        path_proficiency = reader("paths", (self.path,)).get("proficiency")
        if prof_type not in ("armors", "tools", "weapons"):
            raise InvalidValueError

        if prof_type == "tools":
            if self.path == "Assassin" and self.level < 3:
                return
            elif self.klass == "Monk":
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


def get_is_class(klass) -> bool:
    """Returns whether klass is valid."""
    return klass in reader("classes")


def get_is_path(path, klass) -> bool:
    """Returns whether path is a valid path of klass."""
    return path in reader("classes", (klass,)).get("paths")


def get_paths_by_class(klass) -> tuple:
    """Returns a tuple of valid paths for klass."""
    return reader("classes", (klass,)).get("paths")


def get_proficiency_bonus(level: int) -> int:
    """Returns a proficiency bonus value by level."""
    return math.ceil((level / 4) + 1)


def has_class_spells(path) -> bool:
    """Returns whether class path has spells."""
    class_spells = reader("paths", (path,)).get("magic")
    return len(class_spells) is not 0
