from email import message
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
    print(Fore.GREEN + "[++] Thespian is starting using the following options:")

    readout_header = Fore.GREEN + Style.BRIGHT
    readout_value = Fore.YELLOW + Style.BRIGHT
    print(readout_header + "[+] Race: " + readout_value + race)
    print(readout_header + "[+] Subrace: " + readout_value + subrace)
    print(readout_header + "[+] Sex: " + readout_value + sex)
    print(readout_header + "[+] Background: " + readout_value + background)
    print(readout_header + "[+] Alignment: " + readout_value + alignment)
    print(readout_header + "[+] Class: " + readout_value + klass)
    print(readout_header + "[+] Subclass: " + readout_value + subclass)
    print(readout_header + "[+] Level: " + readout_value + str(level))


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
