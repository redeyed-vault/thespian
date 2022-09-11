import sys

from colorama import init, Fore, Style
from prettytable import PrettyTable

from characters import RulesLoader
from httpd import Server
from thespian import thespian


class PromptValueError(ValueError):
    """Class to handle special ValueError exceptions."""


class InteractivePrompt:
    """Class to handle the interactive user prompt."""

    FUNCTIONS_CHARACTER = (
        "alignment",
        "background",
        "class",
        "level",
        "name",
        "race",
        "sex",
        "subclass",
        "subrace",
    )

    FUNCTIONS_UTILITY = (
        "build",
        "help",
        "show",
        "quit",
    )

    def __init__(self) -> None:
        # Init colorama.
        init(autoreset=True)

        # Store user's character selections.
        self.character_options = {
            "alignment": None,
            "background": None,
            "class": None,
            "level": None,
            "name": None,
            "race": None,
            "sex": None,
            "subclass": None,
            "subrace": None,
        }

        # Used to store builder ruleset values.
        self.ruleset_options = dict()

        # Load character builder rulesets.
        for ruleset in RulesLoader:
            ruleset_value = ruleset.value
            if isinstance(ruleset_value, dict):
                self.ruleset_options[ruleset.name] = list(ruleset_value.keys())
            else:
                self.ruleset_options[ruleset.name] = ruleset_value

            self.ruleset_options[ruleset.name].sort()

    def get_params_by_action(self, action_query: str) -> dict | None:
        """Returns all valid parameters for the requested action_query."""
        action_parameter_table = {
            "alignment": "alignments",
            "background": "backgrounds",
            "class": "classes",
            "level": [l for l in range(1, 21)],
            "race": "races",
            "sex": ["Female", "Male"],
            "subclass": "subclasses",
            "subrace": "subraces",
        }

        # If query is not in the actions list table.
        if action_query not in action_parameter_table:
            return None

        # Get value for action from action/parameter table.
        table_value = action_parameter_table[action_query]

        # If not already in list format, pull allowed parameter from listing.
        if isinstance(table_value, str):
            table_value = self.ruleset_options[table_value]

        return table_value

    def _parse_command(self, arguments: str) -> tuple:
        """Parses user argument inputs."""
        arguments = arguments.split(" ")

        # Requires at least one argument.
        if len(arguments) < 1:
            raise PromptValueError(f"Invalid number of arguments specified.")

        # Capture the argument name.
        action = arguments[0]

        # User uses am imvalid action.
        if action == "":
            raise PromptValueError("No action was specified.")
        elif (
            action not in self.FUNCTIONS_CHARACTER
            and action not in self.FUNCTIONS_UTILITY
        ):
            raise PromptValueError(f"Invalid action specified '{action}'.")

        # For actions that don't use parameters.
        if len(arguments) == 1:
            arguments.append("")

        if len(arguments) > 2:
            arguments = arguments[1:]
            arguments = [a.capitalize() for a in arguments]
            parameter = " ".join(arguments)
        else:
            # Store the action parameter.
            parameter = arguments[1]

            # Format parameter to integer if paired with level action.
            # Otherwise just capitalize the first letter.
            if action == "level":
                parameter = int(parameter)
            else:
                parameter = parameter.capitalize()

        return (action, parameter)

    def run(self, message: str = None) -> None:
        """Runs the command prompt."""
        prefix = Fore.GREEN + Style.BRIGHT + "thespian: " + Style.RESET_ALL

        if message is not None:
            prompt_text = prefix + message + "\n"
        else:
            prompt_text = prefix

        # Run the prompt.
        user_input = input(prompt_text)

        # Store action/parameter values.
        try:
            action, parameter = self._parse_command(user_input)
        except PromptValueError as e:
            print(e.__str__())
            self.run()

        if action in self.FUNCTIONS_CHARACTER:
            if action == "level" and parameter not in range(1, 21):
                print("Level parameter must be between 1 - 20.")
            elif action == "name" and parameter == "":
                parameter = "Nameless One"
                print("Name was not set. Using default name.")
            elif action == "sex" and parameter not in ("Female", "Male"):
                print("Sex parameter must be either male or female.")
            else:
                allowed_action_parameters = self.get_params_by_action(action)
                if allowed_action_parameters != None:
                    if parameter not in allowed_action_parameters:
                        print(f"Invalid '{action}' parameter specified '{parameter}'.")
                        return self.run()

                self.character_options[action] = parameter
                print(f"You set your '{action}' to '{parameter}'.")

        # build: Runs character options through thespian.
        # help: Shows application help options.
        # show: Shows current character option selections.
        # quit: Closes the application.
        if action in self.FUNCTIONS_UTILITY:
            if action == "build":
                # Keep running the prompt until all values set.
                # Otherwise return the user's inputs.
                if not all(o is not None for o in self.character_options.values()):
                    print("Not all inputs have been set.")
                else:
                    output = self.character_options
                    character = thespian(
                        output["name"],
                        output["race"],
                        output["subrace"],
                        output["sex"],
                        output["background"],
                        output["alignment"],
                        output["class"],
                        output["subclass"],
                        output["level"],
                    )
                    Server.run(character)
            elif action == "help":
                for action_name in self.FUNCTIONS_CHARACTER:
                    # Capitalize the parameter value.
                    action_parameter = action_name.upper()

                    # Get the appropriate values for the specified action.
                    allowed_param_values = self.get_params_by_action(action_name)

                    # If allowed parameter values is a list.
                    if isinstance(allowed_param_values, list):
                        # Check if list contains non string values.
                        # If so, do conversions.
                        try:
                            for v in allowed_param_values:
                                if isinstance(v, int):
                                    raise ValueError
                        except ValueError:
                            allowed_param_values = [
                                str(v)
                                for v in allowed_param_values
                                if isinstance(v, int)
                            ]

                        allowed_param_values = ", ".join(allowed_param_values)

                    print(
                        "%s <%s> {%s}"
                        % (action_name, action_parameter, allowed_param_values)
                    )
            elif action == "show":
                show = PrettyTable()
                show.field_names = ["Input", "Value"]
                for heading, value in self.character_options.items():
                    if heading not in self.FUNCTIONS_UTILITY:
                        show.add_row([heading, value])
                print(show)
            elif action == "quit":
                try:
                    sys.exit()
                except SystemExit:
                    print("Exiting program.")
    
        # Loop command prompt.
        self.run()


def main() -> None:
    console = InteractivePrompt()
    console.run()


if __name__ == "__main__":
    main()
