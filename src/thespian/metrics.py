from dataclasses import dataclass
import logging
import math
import random

from attributes import roll
from sourcetree import SourceTree

log = logging.getLogger("thespian.metrics")


@dataclass
class AnthropometricCalculator:
    """Used to calculate the height and weight of characters based upon race/subrace."""

    race: str
    sex: str
    subrace: str | None = None

    def _get_height_and_weight_base(self) -> tuple:
        """Gets the base height/weight information for race/subrace."""
        base_height = get_base_height(self.race)
        base_weight = get_base_weight(self.race)

        # If no base race metrics found, check for subrace metrics.
        if base_height is None or base_weight is None:
            base_height = get_base_height(self.subrace)
            base_weight = get_base_weight(self.subrace)

        # If base|sub race metrics info still not found.
        if base_height is None or base_weight is None:
            raise ValueError("No racial/subracial base metrics found.")

        return (base_height, base_weight)

    def _get_metric_data_source(self) -> str:
        """Returns metric data's source race/subrace name i.e Human, Drow, etc."""
        result = get_metrics_by_race(self.race)
        if result is None:
            result = get_metrics_by_race(self.subrace)
            if result is not None:
                return self.subrace
            else:
                raise ValueError("No racial/subracial source could be determined.")

        return self.race

    def calculate(self, factor_sex: bool = False) -> tuple:
        """Calculates character's height and weight."""
        height_values, weight_values = self._get_height_and_weight_base()
        height_pair = height_values.split(",")
        weight_pair = weight_values.split(",")

        # Height formula = base + modifier result
        height_base = int(height_pair[0])
        height_modifier = sum(list(roll(height_pair[1])))
        height_calculation = height_base + height_modifier

        # Weight formula = height modifier * weight modifier + base
        weight_base = int(weight_pair[0])
        weight_modifier = sum(list(roll(weight_pair[1])))
        weight_calculation = (weight_modifier * height_modifier) + weight_base

        # Unofficial rule for height/weight differential by gender
        if factor_sex:
            dominant_sex = get_dominant_sex(self._get_metric_data_source())
            # If no dominant sex found, assume Male is the dominant sex.
            if dominant_sex is None:
                dominant_sex = "Male"
                log.warn(
                    "Dominant gender could not be determined. Default to 'Male'.",
                )

            # Make "non-dominant" sex smaller than the dominant sex.
            if self.sex != dominant_sex:
                # Subtract 0-5 inches from height.
                height_diff = random.randint(0, 5)
                height_calculation = height_calculation - height_diff
                log.warn(
                    f'Using a non-dominant gender height differential of -{height_diff}".',
                )

                # Subtract 15-20% lbs from weight.
                weight_diff = random.randint(15, 20) / 100
                weight_calculation = weight_calculation - math.floor(
                    weight_calculation * weight_diff
                )
                log.warn(
                    f"Using a non-dominant gender weight differential of -{weight_diff}%.",
                )

        if height_calculation < 12:
            height_value = (0, height_calculation)
        else:
            feet = math.floor(height_calculation / 12)
            inches = height_calculation - (feet * 12)
            height_value = (feet, inches)

        return height_value, weight_calculation


def get_base_height(race: str) -> str | None:
    """Returns base height values by race."""
    try:
        return SourceTree.metrics[race]["height"]
    except (AttributeError, KeyError, TypeError):
        return None


def get_base_weight(race: str) -> str | None:
    """Returns base weight values by race."""
    try:
        return SourceTree.metrics[race]["weight"]
    except (AttributeError, KeyError, TypeError):
        return None


def get_dominant_sex(race: str) -> str | None:
    """Returns the physically larger gender by race."""
    try:
        return SourceTree.metrics[race]["dominant"]
    except AttributeError:
        return None


def get_metrics_by_race(race: str) -> str | None:
    """Returns metric data by race."""
    return SourceTree.metrics.get(race)