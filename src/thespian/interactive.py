from colorama import init, Fore, Style

from config.getters import (
    get_pc_alignments,
    get_pc_backgrounds,
    get_pc_classes,
    get_pc_races,
    get_pc_subclasses,
    get_pc_subraces,
)


class ParameterOptionsRouter:

    def __init__(self, option_query: str):
        if len(option_query) < 4:
            raise ValueError("Query must contain at least 4 characters.")

        self.option_query = option_query
        self.parameter_options = {
            "alignment": get_pc_alignments(),
            "background": get_pc_backgrounds(),
            "class": get_pc_classes(),
            "race": get_pc_races(),
            "subclass": get_pc_subclasses(),
            "subrace": get_pc_subraces(),
        }

    @classmethod
    def query_valid_options(cls, option_query):
        router = cls(option_query)
        parameter_values = tuple(router.parameter_options.keys())
        for key in parameter_values:
            if option_query in key:
                return router.parameter_options[key]

        return None


class ThespianInteractivePrompt(ParameterOptionsRouter):

    def __init__(self):
        init(autoreset=True)
        self.user_functions = (
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
        self.utility_functions = ("show")
        self.user_selections = {
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

    def execute(self) -> dict:
        prompt_text = Fore.GREEN + Style.BRIGHT + "thespian: " + Style.RESET_ALL
        user_value = input(prompt_text)

        args = user_value.split(" ")
        if len(args) < 1:
            print(f"Error 1: Invalid number of arguments specified.")
            return self.execute()

        action = args[0]

        if len(args) < 2 and action not in self.utility_functions:
            print(f"Error 1: Invalid action specified '{action}'.")
            return self.execute()

        if len(args) >= 2 and action not in self.user_functions:
            print(f"Error 1: Invalid action specified '{action}'.")
            return self.execute()

        if action in self.utility_functions:
            print(self.user_selections)
            return self.execute()

        if len(args) > 2:
            args = args[1:]
            args = [a.capitalize() for a in args]
            parameter = " ".join(args)
        else:
            parameter = args[1]
            if action == "level":
                parameter = int(parameter)
                if parameter not in range(1, 21):
                    print("Error 2: Level must be between 1 - 20.")
                    return self.execute()
            elif action == "name" and parameter == "":
                print("No name was specified.")
                parameter = "Character"
            elif action == "sex":
                if parameter in ("female", "male"):
                    parameter = parameter.capitalize()
                else:
                    print("Error 3: Sex must be male or female.")
                    return self.execute()
            else:
                if parameter not in ParameterOptionsRouter.query_valid_options(action):
                    print(f"Error 4: Invalid parameter specified for '{action}'.")
                    return self.execute()

        self.user_selections[action] = parameter

        if not all(o is not None for o in self.user_selections.values()):
            return self.execute()
        else:
            return self.user_selections


def main():
    i = ThespianInteractivePrompt()
    print(i.execute())


if __name__ == "__main__":
    main()
