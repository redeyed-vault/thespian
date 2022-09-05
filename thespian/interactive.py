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
        "help",
        "show",
    )

    def __init__(self) -> None:
        # Init colorama.
        init(autoreset=True)

        # Store user's selections.
        self.inputs = {
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

    @staticmethod
    def find_parameters_by_action(action_query: str) -> dict | None:
        """Returns all valid parameters for the requested action_query."""
        ruleset_options = dict()

        # Load character rulesets.
        for ruleset in RulesLoader:
            ruleset_value = ruleset.value
            if isinstance(ruleset_value, dict):
                ruleset_options[ruleset.name] = list(ruleset_value.keys())
            else:
                ruleset_options[ruleset.name] = ruleset_value

            ruleset_options[ruleset.name].sort()

        # Action table list.
        action_parameter_table = {
            "alignment": "alignments", 
            "background": "backgrounds", 
            "class": "classes", 
            "level": [l for l in range(1, 21)], 
            "race": "races", 
            "sex": ["Female", "Male"],
            "subclass": "subclasses", 
            "subrace": "subraces"
        }

        # If query is not in the actions list table.
        if action_query not in action_parameter_table:
            return None

        # Get value for action from action/parameter table.
        action_table_value = action_parameter_table[action_query]

        # If not already in list format, pull allowed parameter from listing.
        if isinstance(action_table_value, str):
            action_table_value = ruleset_options[action_table_value]
        
        return action_table_value

    def _parse_command(self, args: str) -> tuple:
        """Parses user argument inputs."""
        args = args.split(" ")

        # Requires at least one argument.
        if len(args) < 1:
            raise PromptValueError(f"Invalid number of arguments specified.")

        # Capture the argument name.
        action = args[0]

        # User uses am imvalid actopm.
        if action not in self.FUNCTIONS_CHARACTER and action not in self.FUNCTIONS_UTILITY:
            raise PromptValueError(f"Invalid action specified '{action}'.")

        # For actions that don't use parameters.
        if len(args) == 1:
            args.append("")

        if len(args) > 2:
            args = args[1:]
            args = [a.capitalize() for a in args]
            parameter = " ".join(args)
        else:
            # Store the action parameter.
            parameter = args[1]

            # Format parameter to integer if paired with level action.
            # Otherwise just capitalize the first letter.
            if action == "level":
                parameter = int(parameter)
            else:
                parameter = parameter.capitalize()

            if action == "level" and parameter not in range(1, 21):
                raise PromptValueError("Level parameter must be between 1 - 20.")
            elif action == "name" and parameter == "":
                parameter = "Nameless One"
                raise PromptValueError(
                    "Name was not set. Using default name."
                )
            elif action == "sex" and parameter not in ("Female", "Male"):
                raise PromptValueError("Sex parameter must be either male or female.")

        return (action, parameter)

    def run(self, message: str = None) -> dict:
        """Executes the interactive program."""
        if message is not None:
            prompt_text = (
                Fore.GREEN
                + Style.BRIGHT
                + "thespian: "
                + Style.RESET_ALL
                + message
                + "\n"
            )
        else:
            prompt_text = Fore.GREEN + Style.BRIGHT + "thespian: " + Style.RESET_ALL

        # Run the prompt.
        user_input = input(prompt_text)

        try:
            action, parameter = self._parse_command(user_input)
        except PromptValueError as e:
            pass
        except ValueError:
            self.run(e.__str__())

        if action in self.FUNCTIONS_UTILITY:
            if action == "help":
                for action_name in self.FUNCTIONS_CHARACTER:
                    # Capitalize the parameter value.
                    action_parameter = action_name.upper()

                    # Get the appropriate values for the specified action.
                    allowed_param_values = self.find_parameters_by_action(action_name)

                    # If allowed parameter values is a list.
                    if isinstance(allowed_param_values, list):
                        # Check if list contains non string values.
                        # If so, do conversions.
                        try:
                            for v in allowed_param_values:
                                if isinstance(v, int):
                                    raise ValueError
                        except ValueError:
                            allowed_param_values = [str(v) for v in allowed_param_values if isinstance(v, int)]

                        allowed_param_values = ", ".join(allowed_param_values)

                    print('%s <%s> {%s}' % (action_name, action_parameter, allowed_param_values))
            elif action == "show":
                show = PrettyTable()
                show.field_names = ["Input", "Value"]
                for heading, value in self.inputs.items():
                    show.add_row([heading, value])
                print(show)
            return self.run()

        allowed_action_parameters = self.find_parameters_by_action(action)
        if allowed_action_parameters != None:
            if parameter not in allowed_action_parameters:
                print(f"Invalid {action} parameter specified '{parameter}'.")
                return self.run()

        self.inputs[action] = parameter

        # Keep running the prompt until all values set.
        # Otherwise return the user's inputs.
        if not all(o is not None for o in self.inputs.values()):
            return self.run()
        else:
            return self.inputs


def main() -> None:
    console = InteractivePrompt()
    output = console.run()
    character = thespian(
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


if __name__ == "__main__":
    main()
