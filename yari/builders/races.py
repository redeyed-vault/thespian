from random import sample

from .errors import Error
from .._dice import roll
from .._utils import (
    get_is_race,
    get_subraces_by_race,
    has_subraces,
    prompt,
)
from .._yaml import Load


class RaceBuilder:
    def __init__(self, race: str, subrace: str, sex: str = "Female", level: int = 1):
        if not get_is_race(race):
            raise Error(f"Invalid race option specified '{race}'.")

        if has_subraces(race):
            if subrace == "":
                raise Error(f"Subrace option not selected but '{race}' has subraces.")
            allowed_subraces = [x for x in get_subraces_by_race(race)]
            if subrace not in allowed_subraces:
                raise Error(
                    f"Value '{subrace}' is not a valid '{race}' subrace option."
                )

        if sex not in (
            "Female",
            "Male",
        ):
            raise Error(f"Value '{sex}' is not a valid gender option.")

        if isinstance(level, int):
            if not range(1, 21):
                raise Error("Value 'level' must be between 1-20.")
        else:
            raise Error("Value must be of type 'integer'.")

        # Load template for race
        self.race = race
        race_data = Load.get_columns(self.race, source_file="races")
        if race_data is None:
            raise Error(f"Cannot load race template for '{self.race}'.")

        # Set the base armor, tool, weapon proficiencies
        racial_proficiencies = race_data.get("proficiency")
        self.sex = sex
        self.subrace = subrace
        self.level = level
        self.ancestor = None
        self.bonus = race_data.get("bonus")
        self.darkvision = race_data.get("darkvision")
        self.languages = race_data.get("languages")
        self.height = (
            race_data.get("ratio") is not None
            and race_data.get("ratio").get("height")
            or None
        )
        self.weight = (
            race_data.get("ratio") is not None
            and race_data.get("ratio").get("weight")
            or None
        )
        self.size = race_data.get("size")
        self.speed = race_data.get("speed")
        self.traits = race_data.get("traits")
        self.magic_innate = None
        self.skills = (
            race_data.get("skills") is not None and race_data.get("skills") or list()
        )

        for category in racial_proficiencies:
            base_proficiencies = racial_proficiencies.get(category)

            if len(base_proficiencies) >= 2:
                last_value = base_proficiencies[-1]
                if isinstance(last_value, int):
                    del base_proficiencies[-1]
                    base_proficiencies = sample(base_proficiencies, last_value)

            if category == "armors":
                self.armors = base_proficiencies
            elif category == "tools":
                self.tools = base_proficiencies
            elif category == "weapons":
                self.weapons = base_proficiencies

        # Set base resistances
        self.resistances = race_data.get("resistances")

        # Merge traits from base race and subrace (if applicable)
        if subrace != "":
            subrace_data = Load.get_columns(subrace, source_file="subraces")
            if subrace_data is None:
                raise Error(f"Cannot load subrace template for '{subrace}'.")

            for trait, value in subrace_data.items():
                if trait not in race_data:
                    race_data[trait] = subrace_data[trait]
                elif trait == "bonus":
                    for ability, bonus in value.items():
                        race_data[trait][ability] = bonus
                elif trait == "darkvision":
                    race_darkvision = race_data.get(trait)
                    subrace_darkvision = subrace_data.get(trait)
                    if subrace_darkvision is not None:
                        if subrace_darkvision > race_darkvision:
                            self.darkvision = subrace_darkvision
                elif trait == "proficiency":
                    subrace_proficiencies = subrace_data[trait]
                    for category in subrace_proficiencies:
                        added_proficiencies = subrace_proficiencies.get(category)

                        if category == "armors":
                            self.armors = self.armors + added_proficiencies
                        elif category == "tools":
                            self.tools = self.tools + added_proficiencies
                        elif category == "weapons":
                            self.weapons = self.weapons + added_proficiencies
                elif trait == "ratio":
                    ratio = subrace_data.get(trait)
                    if ratio is not None:
                        race_data[trait] = ratio

                    if self.height is None:
                        self.height = ratio.get("height")

                    if self.weight is None:
                        self.weight = ratio.get("weight")
                elif trait == "resistances":
                    added_resistances = subrace_data[trait]
                    self.resistances = self.resistances + added_resistances
                elif trait == "traits":
                    for other in subrace_data.get(trait):
                        race_data[trait].append(other)

        # Assign updated traits list
        self.traits = race_data.get("traits")

    def run(self):
        if "random" in self.bonus:
            bonus_ability_count = self.bonus.get("random")
            del self.bonus["random"]
            if not isinstance(bonus_ability_count, int):
                return
            allowed_bonus_abilities = (
                "Strength",
                "Dexterity",
                "Constitution",
                "Intelligence",
                "Wisdom",
                "Charisma",
            )
            bonus_ability_choices = tuple(self.bonus.keys())
            count_limit = len(allowed_bonus_abilities) - len(bonus_ability_choices)
            if bonus_ability_count > count_limit:
                raise Error(
                    "The number of bonus abilities exceeds the number of allowed ability bonuses."
                )
            bonus_ability_choices = [
                x for x in allowed_bonus_abilities if x not in bonus_ability_choices
            ]
            for _ in range(bonus_ability_count):
                option_list = "\n".join(bonus_ability_choices)
                message = f"Choose your bonus ability:\n\n{option_list}\n"
                bonus_ability_choice = prompt(message, bonus_ability_choices)
                if bonus_ability_choice in bonus_ability_choices:
                    self.bonus[bonus_ability_choice] = 1
                    bonus_ability_choices.remove(bonus_ability_choice)

        # Dragonborn ancestry prompt
        if self.race == "Dragonborn" and isinstance(self.resistances, dict):
            dragon_ancestor = tuple(self.resistances.keys())
            dragon_ancestor_list = "\n".join(dragon_ancestor)
            draconic_ancestry = prompt(
                f"Choose your draconic ancestor's type:\n\n{dragon_ancestor_list}\n\n>",
                dragon_ancestor,
            )
            ancestry_resistances = self.resistances
            self.resistances = []
            self.resistances.append(ancestry_resistances.get(draconic_ancestry))

        # Calculate height/weight
        height_base = self.height.get("base")
        height_modifier = self.height.get("modifier")
        height_modifier = sum(list(roll(height_modifier)))

        weight_base = self.weight.get("base")
        weight_modifier = self.weight.get("modifier")
        weight_modifier = sum(list(roll(weight_modifier)))

        self.height = height_base + height_modifier
        self.weight = (height_modifier * weight_modifier) + weight_base
