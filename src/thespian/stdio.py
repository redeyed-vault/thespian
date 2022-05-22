from argparse import ArgumentTypeError
import time

from colorama import init, Fore, Style


STATUS_ERROR = 1
STATUS_NORMAL = 0
STATUS_WARNING = -1


init(autoreset=True)


class InputRecorder:
    """Stores and recalls user prompt selections."""

    inputs: dict = dict()

    def recall(self, tape: str = None):
        if tape is None:
            return self.inputs

        try:
            return self.inputs[tape]
        except KeyError:
            self.inputs[tape] = set()
            return self.inputs[tape]

    def store(self, tape: str, data: list):
        if tape not in self.inputs:
            self.inputs[tape] = set(data)
        else:
            self.inputs[tape].update(data)


def echo(raw_message: str, status_level: int = STATUS_NORMAL):
    message = raw_message
    if status_level == STATUS_ERROR:
        message = Fore.RED + "[E] " + raw_message
    elif status_level == STATUS_WARNING:
        message = Fore.YELLOW + Style.BRIGHT + "[W] " + raw_message
    elif status_level == STATUS_NORMAL:
        message = Fore.GREEN + Style.BRIGHT + "[N] " + raw_message
    else:
        raise ValueError(
            f"Invalid 'status_level' attribute value '{status_level}' specified."
        )

    print(message)


def initialize(
    race: str,
    subrace: str,
    sex: str,
    background: str,
    klass: str,
    subclass: str,
    level: int,
    threshold: int,
    port: int,
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
        + "\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Threshold: "
        + Fore.YELLOW
        + Style.BRIGHT
        + str(threshold)
        + "\n"
        + Fore.GREEN
        + Style.BRIGHT
        + "[+] Port: "
        + Fore.YELLOW
        + Style.BRIGHT
        + str(port)
    )


def prompt(
    message: str, prompt_options: list | tuple, selected_options: list | tuple = None
):
    time.sleep(2.2)

    if selected_options is not None and not isinstance(selected_options, tuple):
        selected_options = tuple(selected_options)

    # Remove options that are already selected.
    if isinstance(selected_options, (list, tuple)):
        prompt_options = [o for o in prompt_options if o not in selected_options]

    base_opts = {x + 1: y for x, y in enumerate(prompt_options)}
    message = "[P] " + message + "\n"
    for id, option in base_opts.items():
        message += Style.BRIGHT + f"[{id}] {option}\n"
    print(Fore.GREEN + message.strip())

    try:
        user_value = input(Fore.WHITE + "[$] " + Style.RESET_ALL)
        user_value = int(user_value)
    except ValueError:
        echo(
            f"Invalid menu selection: '{user_value}'. Non-numeric value specified.",
            STATUS_ERROR,
        )
        return prompt(
            f"Please try again...",
            base_opts.values(),
            selected_options,
        )
    except (KeyboardInterrupt, RecursionError):
        echo("Keyboard interrupt.", STATUS_WARNING)
        exit()
    else:
        try:
            if user_value not in base_opts:
                raise ArgumentTypeError()
        except ArgumentTypeError:
            echo(
                f"Invalid menu selection: '{user_value}'. Only accepts numeric values 1-{len(base_opts)}.",
                STATUS_ERROR,
            )
            return prompt(
                f"Please try again...",
                base_opts.values(),
                selected_options,
            )

    return base_opts[user_value]
