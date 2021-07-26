from random import sample
from typing import Any, Dict, Text, Type, Union

from colorama import init
from termcolor import colored

init(autoreset=True)

from .sources import Load


def _e(message: Text, color):
    print(colored(message, color, attrs=["bold"]))


def get_character_classes() -> tuple:
    """Returns a tuple of all character classes."""
    return Load.get_row_ids(source_file="classes")


def get_character_feats() -> tuple:
    """Returns a tuple of all character feats."""
    return Load.get_row_ids(source_file="feats")


def get_character_races() -> tuple:
    """Returns a tuple of all character races."""
    return Load.get_row_ids(source_file="races")


def prompt(message: Text, options: Union[list, tuple]) -> Type[str]:
    """
    User input prompter function

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
