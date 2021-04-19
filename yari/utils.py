from math import ceil
from random import sample

from colorama import init
from termcolor import colored

init(autoreset=True)

from parser import Load


def _e(message, color):
    print(colored(message, color, attrs=["bold"]))


def get_character_backgrounds() -> tuple:
    """Returns a tuple of all character backgrounds."""
    return Load.get_row_ids(source_file="backgrounds")


def get_character_classes() -> tuple:
    """Returns a tuple of all character classes."""
    return Load.get_row_ids(source_file="classes")


def get_character_feats() -> tuple:
    """Returns a tuple of all character feats."""
    return Load.get_row_ids(source_file="feats")


def get_character_races() -> tuple:
    """Returns a tuple of all character races."""
    return Load.get_row_ids(source_file="races")


def get_proficiency_bonus(level: int) -> int:
    """
    Returns a proficiency bonus value by level.

    :param int level: Level of character.

    """
    return ceil((level / 4) + 1)


def get_subclasses_by_class(klass: str) -> list:
    """Returns a list of subclasses by klass."""
    return Load.get_columns(klass, "subclasses", source_file="classes")


def get_subraces_by_race(race: str) -> list:
    """Returns a list of subraces by race."""
    return Load.get_columns(race, "subraces", source_file="races")


def merge_dicts(dict1: dict, dict2: (dict, None) = None) -> dict:
    if dict2 is None:
        return dict1

    def is_instance(*objs, obj_type) -> bool:
        for obj in objs:
            if not isinstance(obj, obj_type):
                return False
        return True

    for key, _ in dict2.items():
        if key not in dict1:
            dict1[key] = dict2[key]
        else:
            if is_instance(dict1[key], dict2[key], obj_type=dict):
                if key == "features":
                    new_value = dict()
                    features1 = dict1[key]
                    new_value = features1
                    features2 = dict2[key]
                    for level, features in features2.items():
                        if level in features1:
                            new_value[level] = new_value[level] + features
                        else:
                            new_value[level] = features
                    dict1[key] = new_value
            elif is_instance(dict1[key], dict2[key], obj_type=list):
                if key in ("armors", "tools", "weapons"):
                    dict1[key] = dict1[key] + dict2[key]
    return dict1


def prompt(message: str, options: (list, tuple)) -> str:
    """
    User prompt

    :param str message:
    :param list,tuple options:
    """
    try:
        options = {x: y for x, y in enumerate(options)}
        options_list = "\n\n"
        for id, option in options.items():
            options_list += f"\t{id}.) {option}\n"
        options_list += "\nEnter a number >>"
        user_value = int(input(f"{message} {options_list} ").strip())
        if user_value in options:
            return options[user_value]
        else:
            raise ValueError
    except ValueError:
        return prompt(message, options.values())
    except RecursionError:
        return None


def sample_choice(choices: list) -> list:
    """Randomly returns a list of choices."""
    if len(choices) >= 2:
        last_value = choices[-1]
        if isinstance(last_value, int):
            choices.pop()
            return sample(choices, last_value)
    return choices


def truncate_dict(dict_to_truncate: dict, ceiling: int) -> dict:
    """

    :param dict dict_to_truncate:
    :param int ceiling:
    """
    return {x: y for (x, y) in dict_to_truncate.items() if x <= ceiling}
