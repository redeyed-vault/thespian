from colorama import init, Fore, Style

init(autoreset=True)

from .sources import Load


def _ok(message):
    print(Fore.GREEN + Style.BRIGHT + "[N] " + message)


def _fail(message):
    print(Fore.RED + "[ERR] " + message)


def _warn(message):
    print(Fore.YELLOW + Style.BRIGHT + "[WW] " + message)


def _intro(race, sex, klass, port):
    print(
        Fore.GREEN
        + "[++] Personae is starting using the following options:\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Race: "
        + Fore.YELLOW
        + Style.BRIGHT
        + race
        + "\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Sex: "
        + Fore.YELLOW
        + Style.BRIGHT
        + sex
        + "\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Class: "
        + Fore.YELLOW
        + Style.BRIGHT
        + klass
        + "\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Port: "
        + Fore.YELLOW
        + Style.BRIGHT
        + str(port)
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

    base_opts = {x: y for x, y in enumerate(base_opts)}
    message = "[PP] " + message + "\n"
    for id, option in base_opts.items():
        message += Style.BRIGHT + f"[{id}] {option}\n"
    print(Fore.GREEN + message.strip())

    try:
        user_value = int(input("[**] "))
        if user_value not in base_opts:
            raise ValueError()
    except KeyboardInterrupt:
        print(Fore.YELLOW + Style.BRIGHT + "\n[WW] Keyboard interrupt.")
        exit()
    except ValueError:
        _fail("Invalid selection: " + str(user_value))
        return prompt(
            f"Try again...",
            base_opts.values(),
            selected_opts,
        )
    except RecursionError:
        return None
    else:
        return base_opts[user_value]
