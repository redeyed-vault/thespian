from colorama import init
from termcolor import colored

init(autoreset=True)

from .sources import Load


def _e(message, color):
    print(colored("[N] " + message, color, attrs=["bold"]))


def _intro(race, sex, klass, port):
    def header(value):
        return colored("[+] " + value, "green", attrs=["bold"])

    def option(value):
        return colored(value, "yellow", attrs=["bold"])

    print(
        colored(
            header("Personae is starting using the following options:\n")
            + header("Race: ")
            + option(race)
            + "\n"
            + header("Sex: ")
            + option(sex)
            + "\n"
            + header("Class: ")
            + option(klass)
            + "\n"
            + header("Port: ")
            + option(port),
            attrs=["bold"],
        )
    )


def get_character_classes() -> tuple:
    """Returns a tuple of all character classes."""
    return Load.get_row_ids(source_file="classes")


def get_character_feats() -> tuple:
    """Returns a tuple of all character feats."""
    return Load.get_row_ids(source_file="feats")


def get_character_races() -> tuple:
    """Returns a tuple of all character races."""
    return Load.get_row_ids(source_file="races")


def prompt(message, options, selected_options=None):
    """
    User input prompter function

    :param str message:
    :param list,tuple options:
    :param list,tuple selected_options:

    """
    import time

    time.sleep(2.2)

    if selected_options is not None and not isinstance(selected_options, tuple):
        selected_options = tuple(selected_options)

    if isinstance(selected_options, (list, tuple)):
        options = [o for o in options if o not in selected_options]

    if not isinstance(options, tuple):
        options = tuple(options)

    message = colored("[P] " + message, "green", attrs=["bold"])
    options = {x: y for x, y in enumerate(options)}

    options_list = "\n"
    for id, option in options.items():
        options_list += f"[{id}] {option}\n"
    options_list = colored(options_list, "white", attrs=["bold"])
    options_list += colored("[*]", "green", attrs=["bold"])

    try:
        user_value = int(input(f"{message} {options_list} ").strip())
        if user_value in options:
            return options[user_value]
        else:
            raise ValueError
    except KeyboardInterrupt:
        exit("\nHalting...")
    except ValueError:
        return prompt(message, options.values(), selected_options)
    except RecursionError:
        return None
