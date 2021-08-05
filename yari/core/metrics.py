from .dice import roll
from .errors import Error
from .sources import Load
from .utils import _e


class AnthropometricCalculator:
    def __init__(self, race, sex, subrace=None):
        self.race = race
        self.sex = sex
        self.subrace = subrace

    def _select_base(self):
        base_values = list()
        for characteristic in ("height", "weight"):
            result = Load.get_columns(self.race, characteristic, source_file="metrics")
            if result is None:
                result = Load.get_columns(
                    self.subrace, characteristic, source_file="metrics"
                )
                if result is None:
                    raise Error("No racial base found for height/weight calculation.")
            base_values.append(result)

        height, weight = base_values
        return height, weight

    def _select_origin(self):
        result = Load.get_columns(self.race, source_file="metrics")
        if result is None:
            result = Load.get_columns(self.subrace, source_file="metrics")
            if result is not None:
                return self.subrace
            else:
                raise Error("No racial origin could be determined.")

        return self.race

    def calculate(self, factor_sex=False):
        height_values, weight_values = self._select_base()
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
                self._select_origin(), "dominant", source_file="metrics"
            )
            if dominant_sex is None:
                dominant_sex = "Male"
                _e(
                    "INFO: Dominant gender could not be determined. Default to 'Male'.",
                    "yellow",
                )

            import math

            if self.sex != dominant_sex:
                import random

                # Subtract 0-5 inches from height
                height_diff = random.randint(0, 5)
                height_calculation = height_calculation - height_diff
                _e(
                    f'INFO: Using a non-dominant gender height differential of -{height_diff}".',
                    "yellow",
                )

                # Subtract 15-20% from weight
                weight_diff = random.randint(15, 20) / 100
                weight_calculation = weight_calculation - math.floor(
                    weight_calculation * weight_diff
                )
                _e(
                    f"INFO: Using a non-dominant gender weight differential of -{weight_diff}%.",
                    "yellow",
                )

        if height_calculation < 12:
            height_calculation = (0, height_calculation)
        else:
            feet = math.floor(height_calculation / 12)
            inches = height_calculation - (feet * 12)
            height_calculation = (feet, inches)

        return height_calculation, weight_calculation
