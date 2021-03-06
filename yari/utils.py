from math import ceil

from .builder import parser


def get_character_classes() -> tuple:
    """Returns a tuple of all character classes."""
    return parser.Load.get_row_ids(source_file="classes")


def get_character_feats() -> tuple:
    """Returns a tuple of all character feats."""
    return parser.Load.get_row_ids(source_file="feats")


def get_character_races() -> tuple:
    """Returns a tuple of all character races."""
    return parser.Load.get_row_ids(source_file="races")


def get_proficiency_bonus(level: int) -> int:
    """
    Returns a proficiency bonus value by level.

    :param int level: Level of character.

    """
    return ceil((level / 4) + 1)


def prompt(message: str, options: (list, tuple)) -> str:
    """

    :param str message:
    :param list,tuple options:
    """
    try:
        options_list = "|".join(options)
        user_value = str(input(f"{message} [{options_list}]: "))
        if user_value in options:
            return user_value
        else:
            raise ValueError
    except ValueError:
        return prompt(message, options)
    except RecursionError:
        return ""


def truncate_dict(dict_to_truncate: dict, ceiling: int) -> dict:
    """

    :param dict dict_to_truncate:
    :param int ceiling:
    """
    return {x: y for (x, y) in dict_to_truncate.items() if x <= ceiling}
