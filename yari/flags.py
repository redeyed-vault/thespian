from abc import ABC, abstractmethod
from collections import namedtuple

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
                    flag_options.remove(flag_name)
                    for option in flag_options:
                        if option in self.dataset:
                            self.dataset[option] = []
                    _e(f"INFO: You chose the flagging option '{flag_name}'", "green")
                else:
                    raise Error(
                        "If a flag has multiple options available, it must have two or more options."
                    )

            sewn_flags[flag_name] = int(flag_value)

        return sewn_flags

    def _toDataset(self):
        keywords = tuple(self.dataset.keys())
        dataset = namedtuple("Dataset", keywords)
        self.dataset = dataset(**self.dataset)
        return self.dataset

    @abstractmethod
    def run():
        pass


class BaseClassSeamstress(_FlagSeamstress):
    def __init__(self, klass):
        super(BaseClassSeamstress, self).__init__(
            "classes", klass, ("ability", "skills", "subclass", "tools")
        )
        level = prompt("What level are you?", list(range(1, 21)))
        self.level = int(level)
        _e(f"INFO: Your character level has been set to {self.level}.", "green")
        self.dataset["features"] = {
            x: y for x, y in self.dataset.get("features").items() if x <= self.level
        }
        self.dataset["spellslots"] = self.dataset.get("spellslots").get(self.level)

    def _honor_flags(self, omitted_values=None):
        for flag in self.allowed_flags:
            # _e(f"INFO: Checking for allowed flag '{flag}'...", "yellow")
            if self.flags is None:
                # _e("INFO: No flags specified. Halting flag checking...", "red")
                break
            if flag not in self.flags:
                # _e(f"INFO: Flag '{flag}' not specified. Skipping...", "yellow")
                continue

            if flag == "ability":
                for rank, abilities in self.dataset.get(flag).items():
                    if type(abilities) is list:
                        choice = prompt(f"Choose class option '{flag}':", abilities)
                        self.dataset[flag][rank] = choice
                        _e(f"You chose the ability > '{choice}'", "green")
                self.dataset[flag] = tuple(self.dataset[flag].values())
            else:
                flag_options = self.dataset.get(flag)
                if type(flag_options) is list:
                    if type(omitted_values) is dict and flag in omitted_values:
                        omitted_values = omitted_values.get(flag)
                        if type(omitted_values) is not list:
                            continue
                        flag_options = [x for x in flag_options if x not in omitted_values]

                    num_of_instances = self.flags.get(flag)
                    option_selections = []
                    for _ in range(num_of_instances):
                        chosen_option = prompt(
                            f"Choose class option '{flag}' ({num_of_instances}):",
                            flag_options,
                        )
                        if flag in ("skills", "tools"):
                            option_selections.append(chosen_option)
                        else:
                            option_selections = chosen_option

                        flag_options.remove(chosen_option)
                        _e(
                            f"INFO: You chose > {chosen_option}.",
                            "green",
                        )

                    if (
                        type(option_selections) is list
                        and type(omitted_values) is list
                        and len(omitted_values) > 0
                    ):
                        self.dataset[flag] = option_selections + omitted_values
                    else:
                        self.dataset[flag] = option_selections

        del self.dataset["flags"]

        return self._toDataset()

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class RaceSeamstress(_FlagSeamstress):
    def __init__(self, query_id):
        super(RaceSeamstress, self).__init__(
            "races", query_id, ("armor", "language", "skill", "tool", "weapon")
        )

    def _honor_flags(self):
        for flag in self.allowed_flags:
            if self.flags is None:
                break
            if flag not in self.flags:
                continue
            dataset_value = self.dataset.get(flag)
            if type(dataset_value) is list:
                flag_value = self.flags.get(flag)
                for _ in range(flag_value):
                    options = [
                        x
                        for x in dataset_value
                        if x not in self.dataset.get(flag + "s")
                    ]
                    bonus_language = prompt(
                        f"Choose bonus '{flag}' ({flag_value}):", options
                    )
                    self.dataset[flag + "s"].append(bonus_language)
                    _e(
                        f"INFO: You chose a '{flag}' bonus > {bonus_language}.",
                        "green",
                    )

        del self.dataset["armor"]
        del self.dataset["flags"]
        del self.dataset["language"]
        del self.dataset["skill"]
        del self.dataset["spell"]
        del self.dataset["subraces"]
        del self.dataset["tool"]
        del self.dataset["weapon"]

        return self.dataset

    def run(self):
        return self._honor_flags()


class SubClassSeamstress(_FlagSeamstress):
    def __init__(self, subclass, level=1):
        super(SubClassSeamstress, self).__init__(
            "subclasses", subclass, ("languages", "skills")
        )
        self.dataset["features"] = {
            x: y for x, y in self.dataset.get("features").items() if x <= level
        }

    def _honor_flags(self, omitted_values=None):
        for flag in self.allowed_flags:
            if self.flags is None:
                break
            if flag not in self.flags:
                continue

            bonus_choices = list()
            bonus_options = self.dataset.get(flag)
            bonus_options = self._omit_values(omitted_values, flag, bonus_options)

            num_of_instances = self.flags.get(flag)
            for _ in range(num_of_instances):
                bonus_choice = prompt(
                    f"Choose a bonus '{flag}' ({num_of_instances}):", bonus_options
                )
                bonus_options.remove(bonus_choice)
                bonus_choices.append(bonus_choice)
                _e(f"INFO: You chose the '{flag}' bonus > {bonus_choice}.", "green")
                if len(bonus_choices) > 0:
                    self.dataset[flag] = bonus_choices

        del self.dataset["flags"]

        return self._toDataset()

    def _omit_values(self, values, flag, options):
        if type(values) is dict:
            if flag in values and type(values.get(flag)) is list:
                options = [x for x in options if x not in values.get(flag)]

        return options

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class SubraceSeamstress(_FlagSeamstress):
    def __init__(self, query_id):
        super(SubraceSeamstress, self).__init__(
            "subraces", query_id, ("language", "spell")
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
                        x
                        for x in dataset_value
                        if x not in self.dataset.get(flag + "s")
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
        return self._honor_flags(omitted_values)


# r = RaceSeamstress("Elf")
# r.run()

# r = SubraceSeamstress("High")
# r.run()

a = BaseClassSeamstress("Fighter").run({"skills": ["Persuasion"]})
print(a)

r = SubClassSeamstress(a.subclass).run({"languages": ["Giant"]})
print(r)
