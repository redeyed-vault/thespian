from colorama import init
from termcolor import colored

init(autoreset=True)

from .sources import Load


def _e(message, color):
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


def prompt(message, options):
    """
    User input prompter function

    :param str message:
    :param list,tuple options:
    """
    import time

    time.sleep(3.0)

    try:
        message = colored(">> " + message, "green", attrs=["bold"])
        options = {x: y for x, y in enumerate(options)}
        options_list = "\n\n"
        for id, option in options.items():
            options_list += f"\t{id}.) {option}\n"
        options_list += colored("\nPROMPT: Enter a number >>", "green", attrs=["bold"])
        user_value = int(input(f"{message} {options_list} ").strip())
        if user_value in options:
            return options[user_value]
        else:
            raise ValueError
    except KeyboardInterrupt:
        exit("\nHalting...")
    except ValueError:
        return prompt(message, options.values())
    except RecursionError:
        return None
