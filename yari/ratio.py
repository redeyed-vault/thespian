import math

from yari.dice import roll
from yari.exceptions import RatioValueError
from yari.loader import _read


class RatioGenerator:
    """
    Handles character ratio calculations for height & weight.

    :param str race: Character's chosen race.
    :param str subrace: Character's chosen subrace (if any).
    :param str sex: Character's chosen gender.

    """

    def __init__(self, race: str, subrace: str, sex: str) -> None:
        self.race = race
        self.sex = sex
        self.subrace = subrace

    def _calculate_height(self, height_modifier: int) -> tuple:
        """
        Converts base height and modifier to feet inches.

        :param int height_modifier: Character's height modifier.

        """
        height_base = self._get_base_value("height")
        inches = height_base + height_modifier
        feet = math.floor(inches / 12)
        inches = inches % 12
        return feet, inches

    def _calculate_weight(self, height_modifier: int) -> int:
        """
        Converts base weight and modifier to pounds.

        :param int height_modifier: Character's height modifier.

        """
        weight_base = self._get_base_value("weight")
        weight_modifier = sum(list(roll(self._get_base_modifier("weight"))))
        return (height_modifier * weight_modifier) + weight_base

    def _get_base_modifier(self, ratio: str) -> str:
        """
        Returns character's modifier values by ratio (height/weight).

        :param str ratio: Ratio to use i.e: height or weight.

        """
        try:
            modifier_value = (
                self._get_ratio_base("races", self.race).get(ratio).get("modifier")
            )
        except AttributeError:
            if self.subrace == "":
                raise RatioValueError(f"No modifier value found for '{ratio}' found!")
            else:
                modifier_value = (
                    self._get_ratio_base("subraces", self.subrace)
                    .get(ratio)
                    .get("modifier")
                )
        return modifier_value

    def _get_base_value(self, ratio: str) -> int:
        """
        Returns character's base values by ratio (height/weight).

        :param str ratio: Ratio to use i.e: height or weight.

        """
        try:
            base_value = self._get_ratio_base("races", self.race).get(ratio).get("base")
        except AttributeError:
            if self.subrace == "":
                raise RatioValueError(f"No base value found for '{ratio}' found!")
            else:
                base_value = (
                    self._get_ratio_base("subraces", self.subrace).get(ratio).get("base")
                )
        if (
            self.sex == "Female"
            and self.subrace != "Drow"
            or self.sex == "Male"
            and self.subrace == "Drow"
        ):
            if ratio == "height":
                return base_value - int(base_value * 0.08)
            elif ratio == "weight":
                return base_value - int(base_value * 0.20)
        return base_value

    @staticmethod
    def _get_ratio_base(file: str, race: str):
        """
        Returns character's racial traits by file and race/subrace.

        :param str file: File to use i.e: "races" or "subraces".
        :param str race: Race (or subrace) to retrieve base ratio values for.

        """
        if file not in ("races", "subraces"):
            raise FileNotFoundError(f"The file '{file}' is invalid.")
        return _read(race, "ratio", file=file)

    def calculate(self) -> tuple:
        """Calculates character height/weight with base and modifier."""
        modifier = sum(list(roll(self._get_base_modifier("height"))))
        return self._calculate_height(modifier), self._calculate_weight(modifier)
