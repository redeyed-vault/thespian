from colorama import init, Fore, Style

from config import Guidelines


class ParameterOptionsRouter:
    """Class to gather allowable user prompt action/parameters."""

    def __init__(self):
        self.parameter_options = dict()
        for guideline in Guidelines:
            self.parameter_options[guideline.name] = tuple(guideline.value.keys())

    @classmethod
    def find_parameters(cls, action_query):
        router = cls()
        if len(action_query) < 4:
            raise ValueError("Query must contain at least 4 characters.")

        action_parameter_titles = tuple(router.parameter_options.keys())
        for action in action_parameter_titles:
            if action_query in action:
                return router.parameter_options[action]

        return None


class ThespianInteractivePrompt(ParameterOptionsRouter):
    """Class for the Thespian interactive prompt."""

    USER_FUNCTIONS = (
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
    UTILITY_FUNCTIONS = "show"

    def __init__(self):
        super(ParameterOptionsRouter, self).__init__()
        init(autoreset=True)
        self.user_selections = {
            "alignment": None,
            "background": None,
            "klass": None,
            "level": None,
            "name": None,
            "race": None,
            "sex": None,
            "subclass": None,
            "subrace": None,
        }

    def _parse_(self, args) -> tuple:
        """Parses user argument inputs."""
        args = args.split(" ")

        if len(args) < 1:
            raise ValueError(f"Error 1: Invalid number of arguments specified.")

        action = args[0]

        if len(args) == 1:
            parameter = ""

        if len(args) < 2 and action not in self.UTILITY_FUNCTIONS:
            raise ValueError(f"Error 1: Invalid action specified '{action}'.")

        if len(args) >= 2 and action not in self.USER_FUNCTIONS:
            raise ValueError(f"Error 1: Invalid action specified '{action}'.")

        if len(args) > 2:
            args = args[1:]
            args = [a.capitalize() for a in args]
            parameter = " ".join(args)
        else:
            parameter = args[1]
            if action == "level":
                parameter = int(parameter)
                if parameter not in range(1, 21):
                    raise ValueError("Level parameter must be between 1 - 20.")
            elif action == "name" and parameter == "":
                print("No name was specified.")
                parameter = "Character"
            elif action == "sex":
                if parameter in ("female", "male"):
                    parameter = parameter.capitalize()
                else:
                    raise ValueError("Sex parameter must be either male or female.")
            else:
                if parameter not in ParameterOptionsRouter.get_options(action):
                    raise ValueError(f"Invalid parameter specified for '{action}'.")

        return (action, parameter)

    def execute(self) -> dict:
        """Executes the interactive program."""
        prompt_text = Fore.GREEN + Style.BRIGHT + "thespian: " + Style.RESET_ALL
        user_input = input(prompt_text)

        try:
            action, parameter = self._parse_(user_input)
        except ValueError:
            self.execute()

        if action in self.UTILITY_FUNCTIONS:
            print(self.user_selections)
            return self.execute()

        self.user_selections[action] = parameter

        #print(ParameterOptionsRouter.find_parameters("class"))

        if not all(o is not None for o in self.user_selections.values()):
            return self.execute()
        else:
            return self.user_selections


def main():
    i = ThespianInteractivePrompt()
    print(i.execute())


if __name__ == "__main__":
    main()
