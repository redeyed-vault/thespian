from dataclasses import dataclass

from .dice import roll
from .errors import Error
from .sources import Load
from .utils import _e


@dataclass
class AnthropometricCalculator:
    """Used to calculate the height and weight of characters based upon race/subrace."""

    race: str
    sex: str
    subrace: str = None

    def _get_height_and_weight_base(self):
        """Gets the base height/weight information for race/subrace."""
        base_metric_values = list()
        for characteristic in ("height", "weight"):
            # First, check base race entry for metrics.
            result = Load.get_columns(self.race, characteristic, source_file="metrics")

            # If no base race metrics found, check for subrace metrics.
            if result is None:
                result = Load.get_columns(
                    self.subrace, characteristic, source_file="metrics"
                )

            # If base|sub race metrics not found.
            if result is None:
                raise Error("No racial base metrics found.")

            base_metric_values.append(result)

        # If you don't have two base metric values.
        metric_value_count = len(base_metric_values)
        if metric_value_count != 2:
            raise Error(
                f"Two base metric values must be provided. ({metric_value_count} provided)"
            )

        # pylint: disable=unbalanced-tuple-unpacking
        height, weight = base_metric_values

        return height, weight

    def _get_metric_data_source_race(self):
        """Returns metric data source's race or subrace."""
        result = Load.get_columns(self.race, source_file="metrics")
        if result is None:
            result = Load.get_columns(self.subrace, source_file="metrics")
            if result is not None:
                return self.subrace
            else:
                raise Error("No racial source could be determined.")

        return self.race

    def calculate(self, factor_sex=False):
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
            dominant_sex = Load.get_columns(
                self._get_metric_data_source_race(), "dominant", source_file="metrics"
            )
            if dominant_sex is None:
                dominant_sex = "Male"
                _e(
                    "Dominant gender could not be determined. Default to 'Male'.",
                    "yellow",
                )

            import math

            if self.sex != dominant_sex:
                import random

                # Subtract 0-5 inches from height
                height_diff = random.randint(0, 5)
                height_calculation = height_calculation - height_diff
                _e(
                    f'Using a non-dominant gender height differential of -{height_diff}".',
                    "yellow",
                )

                # Subtract 15-20% from weight
                weight_diff = random.randint(15, 20) / 100
                weight_calculation = weight_calculation - math.floor(
                    weight_calculation * weight_diff
                )
                _e(
                    f"Using a non-dominant gender weight differential of -{weight_diff}%.",
                    "yellow",
                )

        if height_calculation < 12:
            height_calculation = (0, height_calculation)
        else:
            feet = math.floor(height_calculation / 12)
            inches = height_calculation - (feet * 12)
            height_calculation = (feet, inches)

        return height_calculation, weight_calculation
