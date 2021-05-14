from abc import ABC, abstractmethod

from errors import Error
from sources import Load
from utils import _e, prompt


class _SourceFlagSeamstress(ABC):
    def __init__(self, database, query_id):
        result = Load.get_columns(query_id, source_file=database)
        # If dataset is empty, throw error
        if result is None:
            raise Error(f"Data could not be found for '{query_id}'.")

        self.dataset = result
        self.flags = self._sew_flags(self.dataset)

    @abstractmethod
    def _honor_flags(self):
        pass

    def _sew_flags(self, dataset):
        # No flag key found
        if "flags" not in dataset:
            return None

        # If "none" flag specified, do nothing
        if dataset.get("flags") == "none":
            return None

        sewn_flags = dict()
        base_flags = dataset.get("flags").split("|")
        for flag in base_flags:
            if "&&" in flag:
                temp_final_flags = dict()
                flag_option_split = flag.split("&&")
                for option_pair in flag_option_split:
                    if "," not in option_pair:
                        continue
                    (key, value) = option_pair.split(",")
                    if key in sewn_flags:
                        continue
                    temp_final_flags[key] = int(value)
                print(flag_option_split)
            elif "&&" not in flag:
                if "," not in flag:
                    continue
                (key, value) = flag.split(",")
                if key in sewn_flags:
                    continue
                sewn_flags[key] = int(value)
            else:
                raise Error("Unrecognized pattern. Can't sew flag.")

            return sewn_flags


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
        # Show clean result
        print(self.dataset)

    def run(self):
        self._honor_flags()


class SubraceFlagParser(_SourceFlagSeamstress):
    def __init__(self, database, query_id):
        super(SubraceFlagParser, self).__init__(database, query_id)

    def _honor_flags(self):
        pass


p = RaceFlagParser("races", "Lizardfolk")
p.run()
