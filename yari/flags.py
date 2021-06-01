from abc import ABC, abstractmethod

from errors import Error
from sources import Load
from utils import _e, prompt


class _FlagSeamstress(ABC):
    def __init__(self, database, query_id, allowed_flags):
        result = Load.get_columns(query_id, source_file=database)
        if result is None:
            raise Error(f"Data could not be found for '{query_id}'.")

        self.allowed_flags = allowed_flags
        self.dataset = result
        self.flags = self._sew_flags(self.dataset)

    @abstractmethod
    def _honor_flags(self):
        pass

    def _sew_flags(self, dataset):
        if "flags" not in dataset or dataset.get("flags") == "none":
            return None

        sewn_flags = dict()
        base_flags = dataset.get("flags").split("|")
        for flag in base_flags:
            if "," not in flag:
                raise Error("Each flag entry must include a comma.")

            flag_pair = flag.split(",")
            if len(flag_pair) != 2:
                raise Error("Each flag must be a pair (two values only).")

            (flag_name, flag_value) = flag_pair

            if "&&" in flag_name:
                flag_options = flag_name.split("&&")
                if len(flag_options) > 1:
                    flag_name = prompt("Choose your flag option.", flag_options)
                    _e(f"INFO: You chose the flagging option '{flag_name}'", "green")
                else:
                    raise Error(
                        "Each flag if multiple options available must have two or more options."
                    )

            sewn_flags[flag_name] = int(flag_value)

        return sewn_flags

    @abstractmethod
    def run():
        pass


class RaceSeamstress(_FlagSeamstress):
    def __init__(self, database, query_id):
        super(RaceSeamstress, self).__init__(
            database, query_id, ("armor", "language", "skill", "tool", "weapon")
        )

    def _honor_flags(self):
        for flag in self.allowed_flags:
            if flag not in self.flags:
                continue
            dataset_value = self.dataset.get(flag)
            if type(dataset_value) is list:
                flag_value = self.flags.get(flag)
                for _ in range(flag_value):
                    options = [
                        x for x in dataset_value if x not in self.dataset.get(flag + "s")
                    ]
                    bonus_language = prompt(
                        f"Choose bonus '{flag}' ({flag_value}):", options
                    )
                    self.dataset[flag + "s"].append(bonus_language)
                    _e(
                        f"INFO: You chose a '{flag}' bonus > {bonus_language}.",
                        "green",
                    )

        # Remove temporary placeholders
        del self.dataset["armor"]
        del self.dataset["flags"]
        del self.dataset["language"]
        del self.dataset["skill"]
        del self.dataset["tool"]
        del self.dataset["weapon"]
        # Show cleaned dataset result
        return self.dataset

    def run(self):
        print(self._honor_flags())


class SubclassSeamstress(_FlagSeamstress):
    def __init__(self, database, query_id):
        super(SubclassSeamstress, self).__init__(
            database, query_id, ("languages", "skills")
        )

    def _honor_flags(self, omitted_values=None):
        for flag in self.allowed_flags:
            if flag not in self.flags:
                self.dataset[flag] = []
            else:
                bonus_choices = list()
                bonus_options = self.dataset.get(flag)
                if type(omitted_values) is dict:
                    if (
                        flag in omitted_values
                        and type(omitted_values.get(flag)) is list
                    ):
                        bonus_options = [
                            x
                            for x in bonus_options
                            if x not in omitted_values.get(flag)
                        ]
                value = self.flags.get(flag)
                for _ in range(value):
                    bonus_choice = prompt(
                        f"Choose a bonus '{flag}' ({value}):", bonus_options
                    )
                    bonus_options.remove(bonus_choice)
                    bonus_choices.append(bonus_choice)
                    _e(f"INFO: You chose the '{flag}' bonus > {bonus_choice}.", "green")
                    if len(bonus_choices) > 0:
                        self.dataset[flag] = bonus_choices

        del self.dataset["flags"]

        return self.dataset

    def run(self, omitted_values=None):
        print(self._honor_flags(omitted_values))


class SubraceSeamstress(_FlagSeamstress):
    def __init__(self, database, query_id):
        super(SubraceSeamstress, self).__init__(
            database, query_id, ("language", "spell")
        )

    def _honor_flags(self, omitted_values=None):
        for flag in self.allowed_flags:
            if flag not in self.flags:
                continue
            dataset_value = self.dataset.get(flag)
            if type(dataset_value) is list:
                flag_value = self.flags.get(flag)
                for _ in range(flag_value):
                    options = [
                        x for x in dataset_value if x not in self.dataset.get(flag + "s")
                    ]
                    bonus_language = prompt(
                        f"Choose bonus '{flag}' ({flag_value}):", options
                    )
                    self.dataset[flag + "s"].append(bonus_language)
                    _e(
                        f"INFO: You chose a '{flag}' bonus > {bonus_language}.",
                        "green",
                    )

        del self.dataset["flags"]
        del self.dataset["language"]
        del self.dataset["spell"]
        
        return self.dataset

    def run(self, omitted_values=None):
        print(self._honor_flags(omitted_values))


# r = RaceSeamstress("races", "Lizardfolk")
# r.run()

r = SubraceSeamstress("subraces", "High")
r.run()

# c = SubclassSeamstress("subclasses", "Samurai")
# c.run({"languages": ["Giant"]})
