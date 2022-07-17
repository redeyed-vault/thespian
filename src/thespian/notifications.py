import time

from colorama import init, Fore, Style


STATUS_ERROR = 1
STATUS_NORMAL = 0
STATUS_WARNING = -1


init(autoreset=True)


def echo(message: str, status_level: int = STATUS_NORMAL) -> None:
    """Outputs status messages."""
    if status_level == STATUS_ERROR:
        message = Fore.RED + "[E] " + message
    elif status_level == STATUS_WARNING:
        message = Fore.YELLOW + Style.BRIGHT + "[W] " + message
    elif status_level == STATUS_NORMAL:
        message = Fore.GREEN + Style.BRIGHT + "[N] " + message
    print(message)


def initialize(
    race: str,
    subrace: str,
    sex: str,
    background: str,
    alignment: str,
    klass: str,
    subclass: str,
    level: int,
):
    print(
        Fore.GREEN
        + "[++] Thespian is starting using the following options:\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Race: "
        + Fore.YELLOW
        + Style.BRIGHT
        + race
        + "\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Subrace: "
        + Fore.YELLOW
        + Style.BRIGHT
        + subrace
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
        + "[+] Background: "
        + Fore.YELLOW
        + Style.BRIGHT
        + background
        + "\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Alignment: "
        + Fore.YELLOW
        + Style.BRIGHT
        + alignment
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
        + "[+] Subclass: "
        + Fore.YELLOW
        + Style.BRIGHT
        + subclass
        + "\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Level: "
        + Fore.YELLOW
        + Style.BRIGHT
        + str(level)
    )


def prompt(
    message: str, prompt_options: list | tuple, selected_options: set = None
) -> str:
    """Runs user prompt menu."""
    time.sleep(2.2)

    # Sets used to keep the selected_option values unique.
    # Forces conversion of selected_options to a tuple.
    # Code breaks otherwise when filtering out already chosen options.
    if isinstance(selected_options, set):
        selected_options = tuple(selected_options)

    # Remove options that are already selected.
    if isinstance(selected_options, (list, tuple)):
        prompt_options = [o for o in prompt_options if o not in selected_options]

    prompt_options = {x + 1: y for x, y in enumerate(prompt_options)}
    message = "[P] " + message + "\n"
    for id, option in prompt_options.items():
        message += Style.BRIGHT + f"[{id}] {option}\n"
    print(Fore.GREEN + message.strip())

    try:
        user_value = int(input(Fore.WHITE + "[$] " + Style.RESET_ALL))
    except ValueError:
        echo(
            f"Only numeric values are permitted.",
            STATUS_ERROR,
        )
        return prompt(
            f"Please try again...",
            prompt_options.values(),
            selected_options,
        )

    try:
        if user_value not in prompt_options:
            raise ValueError()
    except ValueError:
        echo(
            f"Invalid selection. Only values between 1-{len(prompt_options)} are allowed.",
            STATUS_ERROR,
        )
        return prompt(
            f"Please try again...",
            prompt_options.values(),
            selected_options,
        )

    return prompt_options[user_value]
