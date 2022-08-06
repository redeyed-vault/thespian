import time

from colorama import init, Fore, Style


STATUS_ERROR = 1
STATUS_NORMAL = 0
STATUS_WARNING = -1


init(autoreset=True)


class PromptRecorder:
    """Class to store/recall user prompt selections."""

    prompt_inputs: dict = dict()

    def recall(self, prompt_category: str) -> dict:
        """Returns/creates (if non-existent) prompt saved to a specified category."""
        try:
            return self.prompt_inputs[prompt_category]
        except KeyError:
            self.prompt_inputs[prompt_category] = set()
            return self.prompt_inputs[prompt_category]

    def store(self, prompt_category: str, prompt_inputs: list) -> None:
        """Stores prompts to a specified category."""
        if prompt_category not in self.prompt_inputs:
            self.prompt_inputs[prompt_category] = set(prompt_inputs)
        else:
            self.prompt_inputs[prompt_category].update(prompt_inputs)


def echo(message: str, status_level: int = STATUS_NORMAL) -> None:
    """Outputs color coded status messages."""
    if status_level == STATUS_ERROR:
        message = Fore.RED + "[E] " + message
    elif status_level == STATUS_WARNING:
        message = Fore.YELLOW + Style.BRIGHT + "[W] " + message
    elif status_level == STATUS_NORMAL:
        message = Fore.GREEN + Style.BRIGHT + "[N] " + message

    print(message)


def init_status(
    race: str,
    subrace: str,
    sex: str,
    background: str,
    alignment: str,
    klass: str,
    subclass: str,
    level: int,
) -> None:
    """Shows Thespian init status."""
    print(Fore.GREEN + "[++] Thespian is starting using the following options:")

    status_title = Fore.GREEN + Style.BRIGHT + "[+] "
    status_value = Fore.YELLOW + Style.BRIGHT
    print(status_title + "Race: " + status_value + race)
    print(status_title + "Subrace: " + status_value + subrace)
    print(status_title + "Sex: " + status_value + sex)
    print(status_title + "Background: " + status_value + background)
    print(status_title + "Alignment: " + status_value + alignment)
    print(status_title + "Class: " + status_value + klass)
    print(status_title + "Subclass: " + status_value + subclass)
    print(status_title + "Level: " + status_value + str(level))


def prompt(
    message: str, prompt_options: list | tuple, selected_options: set = None
) -> str:
    """Runs user prompt."""
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
            raise ValueError
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
