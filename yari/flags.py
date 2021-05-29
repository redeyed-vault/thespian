from abc import ABC, abstractmethod

from errors import Error
from sources import Load
from utils import _e, prompt


class _SourceFlagSeamstress(ABC):
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
        if "flags" not in dataset:
            return None
        if dataset.get("flags") == "none":
            return None

        sewn_flags = dict()
        base_flags = dataset.get("flags").split("|")
        for flag in base_flags:
            if "," not in flag:
                raise Error("Malformed error 1")

            flag_pair = flag.split(",")
            if len(flag_pair) != 2:
                raise Error("Malformed error 2")

            (flag_name, flag_value) = flag_pair

            if "&&" in flag_name:
                flag_options = flag_name.split("&&")
                if len(flag_options) > 1:
                    flag_name = prompt("Choose your flag option.", flag_options)
                    _e(f"INFO: You chose the flagging option '{flag_name}'", "green")
                else:
                    raise Error("Malformed error 3")

            sewn_flags[flag_name] = int(flag_value)

        return sewn_flags

    @abstractmethod
    def run():
        pass


class RaceFlagParser(_SourceFlagSeamstress):
    def __init__(self, database, query_id):
        super(RaceFlagParser, self).__init__(database, query_id)

    def _honor_flags(self):
        # Loop through the loaded dataset
        # Check if dataset key matches flag keys
        for key, value in self.dataset.items():
            if key not in self.flags:
                continue
            if type(value) is list:
                if key not in ("armor", "language", "skill", "tool", "weapon"):
                    continue
                implementation_count = self.flags.get(key)
                for _ in range(implementation_count):
                    options = [x for x in value if x not in self.dataset.get(key + "s")]
                    bonus_language = prompt(
                        f"Choose bonus '{key}' ({implementation_count}):", options
                    )
                    self.dataset[key + "s"].append(bonus_language)
                    _e(
                        f"INFO: You chose the bonus '{key}' > {bonus_language}.",
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
        print(self.dataset)

    def run(self):
        self._honor_flags()


class SubclassFlagParser(_SourceFlagSeamstress):
    def __init__(self, database, query_id):
        super(SubclassFlagParser, self).__init__(
            database, query_id, ("languages", "skills")
        )

    def _honor_flags(self):
        for flag in self.allowed_flags:
            if flag not in self.flags:
                self.dataset[flag] = []
            else:
                bonus_choices = list()
                bonus_options = self.dataset.get(flag)
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

        print(self.dataset)

    def run(self):
        self._honor_flags()


class SubraceFlagParser(_SourceFlagSeamstress):
    def __init__(self, database, query_id):
        super(SubraceFlagParser, self).__init__(database, query_id)

    def _honor_flags(self):
        pass


# r = RaceFlagParser("races", "Lizardfolk")
# r.run()

c = SubclassFlagParser("subclasses", "Samurai")
c.run()
