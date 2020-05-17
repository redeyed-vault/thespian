import math
import random

from yari.collect import fuse
from yari.reader import reader


class _Classes:
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
        if self.class_ == "_Classes":
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
        """Assigns abilities where classes might have a choice of a primary ability.

            - Fighter: Strength|Dexterity
            - Fighter: Constitution|Intelligence
            - Ranger: Dexterity|Strength
            - Rogue: Charisma|Intelligence
            - Wizard: Constitution|Dexterity
        """
        class_abilities = reader("classes", (self.class_, "abilities",))
        if self.class_ == "Cleric":
            class_abilities[2] = random.choice(class_abilities[2])
        elif self.class_ in ("Fighter", "Ranger"):
            ability_choices = class_abilities.get(1)
            class_abilities[1] = random.choice(ability_choices)
            if self.class_ == "Fighter" and self.path != "Eldritch Knight":
                class_abilities[2] = "Constitution"
            elif self.class_ == "Fighter" and self.path == "Eldritch Knight":
                class_abilities[2] = "Intelligence"
            else:
                class_abilities[2] = class_abilities.get(2)
        elif self.class_ == "Rogue":
            if self.path != "Arcane Trickster":
                class_abilities[2] = "Charisma"
            else:
                class_abilities[2] = "Intelligence"
        elif self.class_ == "Wizard":
            ability_choices = class_abilities.get(2)
            class_abilities[2] = random.choice(ability_choices)
        return class_abilities

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
        """Generates hit die and point totals."""
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
        else:
            self.features["magic"] = dict()

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


class Barbarian(_Classes):
    def __init__(self, **kw) -> None:
        super(Barbarian, self).__init__(**kw)


class Bard(_Classes):
    def __init__(self, **kw) -> None:
        super(Bard, self).__init__(**kw)


class Cleric(_Classes):
    def __init__(self, **kw) -> None:
        super(Cleric, self).__init__(**kw)


class Druid(_Classes):
    def __init__(self, **kw) -> None:
        super(Druid, self).__init__(**kw)


class Fighter(_Classes):
    def __init__(self, **kw) -> None:
        super(Fighter, self).__init__(**kw)


class Monk(_Classes):
    def __init__(self, **kw) -> None:
        super(Monk, self).__init__(**kw)


class Paladin(_Classes):
    def __init__(self, **kw) -> None:
        super(Paladin, self).__init__(**kw)


class Ranger(_Classes):
    def __init__(self, **kw) -> None:
        super(Ranger, self).__init__(**kw)


class Rogue(_Classes):
    def __init__(self, **kw) -> None:
        super(Rogue, self).__init__(**kw)


class Sorcerer(_Classes):
    def __init__(self, **kw) -> None:
        super(Sorcerer, self).__init__(**kw)


class Warlock(_Classes):
    def __init__(self, **kw) -> None:
        super(Warlock, self).__init__(**kw)


class Wizard(_Classes):
    def __init__(self, **kw) -> None:
        super(Wizard, self).__init__(**kw)


def get_is_class(klass) -> bool:
    """Returns whether klass is a valid class."""
    return klass in tuple(reader("classes").keys())


def get_is_path(path, klass) -> bool:
    """Returns whether path is a valid path of klass."""
    return path in tuple(reader("classes", (klass, "paths")))


def get_paths_by_class(klass) -> tuple:
    """Returns a tuple of valid paths for klass."""
    return tuple(reader("classes", (klass, "paths")))


def has_class_spells(path) -> bool:
    """Returns whether class has spells."""
    class_spells = reader("paths", (path,)).get("magic")
    return len(class_spells) is not 0


def get_proficiency_bonus(level: int) -> int:
    """Returns a proficiency bonus value by level."""
    return math.ceil((level / 4) + 1)
