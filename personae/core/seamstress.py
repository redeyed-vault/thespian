from collections import namedtuple

from .blueprint import (
    BaseClassBlueprint,
    BaseRaceBlueprint,
    SubClassBlueprint,
    SubRaceBlueprint,
)
from .errors import SeamstressError
from .sources import Load
from .utils import _ok, prompt


class Seamstress:
    """Builds character data objects (tapestries)."""

    def __init__(self):
        self.pattern = None
        self.threads = None

    def _toTapestry(self):
        pattern = namedtuple("MyTapestry", self.threads)
        return pattern(**self.pattern)

    def _toDict(self):
        return self.pattern

    def view(self, to_dict=False):
        if not to_dict:
            self.pattern = self._toTapestry()
        else:
            self.pattern = self._toDict()

        return self.pattern

    def weave(self, a, b=None):
        if not isinstance(a, dict):
            raise SeamstressError("First parameter must be of type 'dict'.")
        if not isinstance(b, dict) and b is not None:
            raise SeamstressError(
                "Second parameter must be of type 'dict' or 'NoneType'."
            )

        # Remove flags index for original data, if applicable.
        if "flags" in a:
            del a["flags"]

        # Remove flags index from "sub" data, if applicable.
        if type(b) is dict and "flags" in b:
            del b["flags"]

        # Merge a and b dictionaries, if applicable.
        if isinstance(b, dict):
            for key, value in b.items():
                # If index not availble in root dictionary.
                if key not in a:
                    a[key] = value
                    continue

                # Merge dicts
                if isinstance(value, dict):
                    a_dict = a.get(key)
                    for subkey, subvalue in value.items():
                        if a_dict is None:
                            break
                        if subkey not in a_dict:
                            try:
                                a[key][subkey] = subvalue
                            except IndexError:
                                a[key] = subvalue
                        else:
                            a[key][subkey] = a_dict.get(subkey) + subvalue
                    continue

                # Merge integers
                if isinstance(value, int):
                    a_int = a.get(key)
                    if not isinstance(a_int, int):
                        continue
                    if value > a_int:
                        a[key] = value

                # Merge lists
                if isinstance(value, list):
                    a_list = a.get(key)
                    if isinstance(a_list, list):
                        a[key] = list(set(a_list + value))

        # Resort dictionary by keys
        raw_dataset = a
        self.threads = list(raw_dataset.keys())
        self.threads.sort()
        sorted_dataset = {}
        for keyword in self.threads:
            if keyword in raw_dataset:
                sorted_dataset[keyword] = raw_dataset.get(keyword)

        self.pattern = sorted_dataset


class ClassSeamstress(Seamstress):
    """Generates character's class tapestry."""

    def __init__(self, klass, omitted_values=None):
        a = BaseClassBlueprint(klass).run(omitted_values)
        b = None
        subclass = a.get("subclass")
        if subclass is not None:
            b = SubClassBlueprint(subclass, a.get("level")).run(omitted_values)

        super().__init__()
        self.weave(a, b)
        self.data = self.view(True)


class RaceSeamstress(Seamstress):
    """Generates character's racial tapestry."""

    def __init__(self, race, sex):
        a = BaseRaceBlueprint(race).run()
        subrace = a.get("subrace")
        if not isinstance(subrace, str) or subrace == "":
            b = None
        else:
            b = SubRaceBlueprint(subrace).run(a)

        from .metrics import AnthropometricCalculator

        c = AnthropometricCalculator(race, sex, subrace)
        height, weight = c.calculate(True)
        a["height"] = height
        a["weight"] = weight
        a["sex"] = sex

        super().__init__()
        self.weave(a, b)
        self.data = self.view(True)
