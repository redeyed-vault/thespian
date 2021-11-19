from colorama import init
from termcolor import colored

init(autoreset=True)

from .sources import Load


def _ok(message):
    print(colored("[N] " + message, "green", attrs=["bold"]))


def _fail(message):
    print(colored("[N] " + message, "red", attrs=["bold"]))


def _warn(message):
    print(colored("[N] " + message, "yellow", attrs=["bold"]))


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


def prompt(message, base_opts, selected_opts=None):
    """
    User input prompter function

    :param str message:
    :param list,tuple base_opts:
    :param list,tuple selected_opts:

    """
    import time

    time.sleep(2.2)

    if selected_opts is not None and not isinstance(selected_opts, tuple):
        selected_opts = tuple(selected_opts)

    if isinstance(selected_opts, (list, tuple)):
        base_opts = [o for o in base_opts if o not in selected_opts]

    if not isinstance(base_opts, tuple):
        base_opts = tuple(base_opts)

    message = colored("[P] " + message, "green", attrs=["bold"])
    base_opts = {x: y for x, y in enumerate(base_opts)}

    options_list = "\n"
    for id, option in base_opts.items():
        options_list += f"[{id}] {option}\n"
    options_list = colored(options_list, "white", attrs=["bold"])
    options_list += colored("[*]", "green", attrs=["bold"])

    try:
        user_value = int(input(f"{message} {options_list} ").strip())
        if user_value not in base_opts:
            raise ValueError()
    except KeyboardInterrupt:
        exit("\nHalting...")
    except ValueError:
        return prompt(message, base_opts.values(), selected_opts)
    except RecursionError:
        return None
    else:
        return base_opts[user_value]
