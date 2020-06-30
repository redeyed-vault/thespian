import math

from yari.dice import roll
from yari.reader import reader


class RatioGenerator:
    """Handles character ratio calculations for height & weight."""

    def __init__(self, race: str, subrace: str) -> None:
        """
        Args:
            race (str): Character's chosen race.
            subrace (str): Character's chosen subrace (if any).

        """
        self.race = race
        self.subrace = subrace

    def _calculate_height(self, height_modifier: int) -> tuple:
        """Converts base height and modifier to feet inches.

        Args:
            height_modifier (int): Height modifier.

        """
        height_base = self._get_base("height")
        inches = height_base + height_modifier
        feet = math.floor(inches / 12)
        inches = inches % 12
        return feet, inches

    def _calculate_weight(self, height_modifier: int) -> int:
        """Converts base weight and modifier to pounds.

        Args:

            height_modifier (int): Height modifier.
        """
        weight_base = self._get_base("weight")
        weight_modifier = sum(list(roll(self._get_modifier("weight"))))
        weight_modifier = height_modifier * weight_modifier
        return weight_base + weight_modifier

    def _get_base(self, ratio: str) -> int:
        """Returns character's base values by ratio (height/weight).

        Args:
            ratio (str): Ratio to use i.e: height or weight.

        """
        try:
            racial_traits = self._get_traits("races", self.race).get(ratio).get("base")
        except AttributeError:
            racial_traits = (
                self._get_traits("subraces", self.subrace).get(ratio).get("base")
            )
        return racial_traits

    def _get_modifier(self, ratio: str) -> str:
        """Returns character's modifier values by ratio (height/weight).

        Args:
            ratio (str): Ratio to use i.e: height or weight.

        """
        try:
            racial_traits = (
                self._get_traits("races", self.race).get(ratio).get("modifier")
            )
        except AttributeError:
            racial_traits = (
                self._get_traits("subraces", self.subrace).get(ratio).get("modifier")
            )
        return racial_traits

    @staticmethod
    def _get_traits(file: str, race_or_subrace: str):
        """Returns character's racial traits by file and race/subrace.

        Args:
            file (str): File to use i.e: "races" or "subraces".
            race_or_subrace (str): Character race/subrace to retreive traits for.

        """
        if file not in ("races", "subraces"):
            raise FileNotFoundError("invalid file selection")
        return reader(file, (race_or_subrace,)).get("traits")

    def calculate(self) -> tuple:
        """Calculates character height/weight with base and modifier."""
        modifier = sum(list(roll(self._get_modifier("height"))))
        return self._calculate_height(modifier), self._calculate_weight(modifier)
