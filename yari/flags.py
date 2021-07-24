from abc import ABC, abstractmethod
from collections import namedtuple

from dice import roll
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

    @abstractmethod
    def run():
        pass


class _BaseClassSeamstress(_FlagSeamstress):
    def __init__(self, klass):
        super(_BaseClassSeamstress, self).__init__(
            "classes", klass, ("ability", "skills", "subclass", "tools")
        )
        level = int(prompt("What level are you?", list(range(1, 21))))
        _e(f"INFO: Your character level has been set to {level}.", "green")
        self.dataset["features"] = {
            x: y for x, y in self.dataset.get("features").items() if x <= level
        }
        self.dataset["level"] = level

        # Calculate hit die/points
        hit_die = int(self.dataset.get("hit_die"))
        self.dataset["hit_die"] = f"{level}d{hit_die}"
        self.dataset["hp"] = hit_die
        if level > 1:
            new_level = level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            self.dataset["hp"] += sum(die_rolls)

        self.dataset["spellslots"] = self.dataset.get("spellslots").get(level)

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
                    if type(abilities) is not list:
                        continue
                    choice = prompt(f"Choose class option '{flag}':", abilities)
                    self.dataset[flag][rank] = choice
                    _e(f"You chose the ability > '{choice}'", "green")
                self.dataset[flag] = tuple(self.dataset[flag].values())
            else:
                num_of_instances = self.flags.get(flag)
                flag_options = self.dataset.get(flag)
                if type(flag_options) is list:
                    if type(omitted_values) is dict and flag in omitted_values:
                        omitted_values = omitted_values.get(flag)
                        if type(omitted_values) is not list:
                            continue
                        flag_options = [
                            x for x in flag_options if x not in omitted_values
                        ]

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

        ability = self.dataset.get("ability")
        if type(ability) is dict:
            self.dataset["ability"] = tuple(ability.values())

        return self.dataset

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class _SubClassSeamstress(_FlagSeamstress):
    def __init__(self, subclass, level=1):
        super(_SubClassSeamstress, self).__init__(
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

        return self.dataset

    def _omit_values(self, values, flag, options):
        if type(values) is dict:
            if flag in values and type(values.get(flag)) is list:
                options = [x for x in options if x not in values.get(flag)]

        return options

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class _BaseRaceSeamstress(_FlagSeamstress):
    def __init__(self, race):
        super(_BaseRaceSeamstress, self).__init__(
            "races",
            race,
            ("armors", "languages", "skills", "subrace", "tools", "weapons"),
        )

    def _honor_flags(self):
        # Set alignment
        base_alignment_options=(
            "Chaotic Evil",
            "Chaotic Good",
            "Chaotic Neutral",
            "Lawful Evil",
            "Lawful Good",
            "Lawful Neutral",
            "Neutral Evil",
            "Neutral Good",
            "True Neutral",
        )
        alignment = prompt("What is your chosen alignment?", base_alignment_options)
        self.dataset["alignment"] = alignment
        _e(f"INFO: You set your alignment to > {alignment}.", "green")

        # Set base ancestry
        base_ancestry_options = self.dataset.get("ancestry")
        if len(base_ancestry_options) == 0:
            self.dataset["ancestry"] = None
        else:
            ancestry = prompt("What is your draconic ancestry?", base_ancestry_options)
            self.dataset["ancestry"] = ancestry
            self.dataset["resistances"] = [
                self.dataset.get("resistances").get(ancestry)
            ]
            _e(f"INFO: You set your draconic ancestry to > {ancestry}.", "green")

        # Set base languages
        base_language_options = self.dataset.get("languages")
        base_languages = list()
        for language in base_language_options:
            if type(language) is list:
                base_languages += language
                base_language_options.remove(language)
        self.dataset["languages"] = base_languages

        # Set base spells
        # base_spells = list()
        base_spell_options = self.dataset.get("spells")
        if len(base_spell_options) != 0:
            if type(base_spell_options) is dict:
                caster_level = int(
                    prompt("What is your caster level?", list(range(1, 21)))
                )
                base_spells = []
                for req_level, spell_list in base_spell_options.items():
                    if req_level <= caster_level:
                        base_spells += spell_list
                self.dataset["spells"] = base_spells
                _e(f"INFO: You set your caster level to > {caster_level}.", "green")

        # Set base subrace
        base_subrace_options = self.dataset.get("subrace")
        if len(base_subrace_options) == 0:
            self.dataset["subrace"] = None
        else:
            subrace = prompt("Choose your 'subrace'", base_subrace_options)
            self.dataset["subrace"] = subrace
            _e(f"INFO: You set your subrace to > {subrace}.", "green")

        # No flags actually specified
        if self.flags is None:
            return self.dataset

        # Determine bonus languages, skills, proficiencies
        for proficiency in ("armors", "languages", "skills", "tools", "weapons"):
            if proficiency not in self.flags:
                continue
            base_skills = list()
            base_skill_options = self.dataset.get(proficiency)
            if len(base_skill_options) > 0:
                num_of_instances = self.flags.get(proficiency)
                for _ in range(num_of_instances):
                    choice = prompt(
                        f"Choose your '{proficiency}' proficiency ({num_of_instances})",
                        base_skill_options,
                    )
                    base_skills.append(choice)
                    base_skill_options.remove(choice)
                    _e(
                        f"INFO: You chose the '{proficiency}' proficiency > {choice}.",
                        "green",
                    )
                self.dataset[proficiency] = base_skills

        return self.dataset

    def run(self):
        return self._honor_flags()


class _SubRaceSeamstress(_FlagSeamstress):
    def __init__(self, subrace):
        super(_SubRaceSeamstress, self).__init__(
            "subraces", subrace, ("language", "spell")
        )

    def _honor_flags(self, omitted_values=None):
        # No flags actually specified
        if self.flags is None:
            return self.dataset

        # Set base spells
        base_spell_options = self.dataset.get("spells")
        if len(base_spell_options) != 0:
            base_spells = []
            if type(base_spell_options) is dict:
                caster_level = int(
                    prompt("What is your caster level?", list(range(1, 21)))
                )
                for req_level, spell_list in base_spell_options.items():
                    if req_level <= caster_level:
                        base_spells += spell_list
                self.dataset["spells"] = base_spells
                _e(f"INFO: You set your caster level to > {caster_level}.", "green")
            if type(base_spell_options) is list:
                if "spells" in self.flags:
                    num_of_instances = self.flags.get("spells")
                    for _ in range(num_of_instances):
                        spell_choice = prompt(
                            f"Choose your 'spells' proficiency ({num_of_instances})",
                            base_spell_options,
                        )
                        base_spells.append(spell_choice)
                        base_spell_options.remove(spell_choice)
                        _e(f"You selected the spell > '{spell_choice}'", "green")
                    self.dataset["spells"] = base_spells

        # Determine bonus languages, skills, proficiencies
        for proficiency in ("armors", "languages", "skills", "tools", "weapons"):
            if proficiency not in self.flags:
                continue
            base_skills = list()
            base_skill_options = self.dataset.get(proficiency)
            if len(base_skill_options) > 0:
                num_of_instances = self.flags.get(proficiency)
                for _ in range(num_of_instances):
                    choice = prompt(
                        f"Choose your '{proficiency}' proficiency ({num_of_instances})",
                        base_skill_options,
                    )
                    base_skills.append(choice)
                    base_skill_options.remove(choice)
                    _e(
                        f"INFO: You chose the '{proficiency}' proficiency > {choice}.",
                        "green",
                    )
                self.dataset[proficiency] = base_skills

        return self.dataset

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class DataSet:
    def __init__(self):
        self.dataset = None
        self.keywords = None

    def _toDataset(self):
        dataset = namedtuple("Dataset", self.keywords)
        return dataset(**self.dataset)

    def _toDict(self):
        return self.dataset

    def parse_dataset(self, a, b=None):
        if type(a) is not dict:
            raise Error("First parameter must be of type 'dict'.")
        if type(b) is not dict and type(b) is not None:
            raise Error("Second parameter must be of type 'dict' or 'NoneType'.")

        if "flags" in a:
            del a["flags"]
        if type(b) is dict and "flags" in b:
            del b["flags"]

        if type(b) is dict:
            for key, value in b.items():
                if key not in a:
                    a[key] = value
                    continue
                if type(value) is dict:
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
                if type(value) is int:
                    a_int = a.get(key)
                    if type(a_int) is not int:
                        continue
                    if value > a_int:
                        a[key] = value
                if type(value) is list:
                    a_list = a.get(key)
                    if type(a_list) is list:
                        a[key] = list(set(a_list + value))

        raw_dataset = a
        self.keywords = list(raw_dataset.keys())
        self.keywords.sort()
        sorted_dataset = {}
        for keyword in self.keywords:
            if keyword in raw_dataset:
                sorted_dataset[keyword] = raw_dataset.get(keyword)

        self.dataset = sorted_dataset

    def read_dataset(self, to_dict=False):
        if not to_dict:
            self.dataset = self._toDataset()
        else:
            self.dataset = self._toDict()

        return self.dataset


class ClassSeamstress(DataSet):
    def __init__(self, klass, omitted_values=None):
        a = _BaseClassSeamstress(klass).run(omitted_values)
        b = _SubClassSeamstress(a.get("subclass"), a.get("level")).run(omitted_values)

        super(DataSet, self).__init__()
        self.parse_dataset(a, b)
        self.data = self.read_dataset(True)


class RaceSeamstress(DataSet):
    def __init__(self, race, sex):
        a = _BaseRaceSeamstress(race).run()
        subrace = a.get("subrace")
        if subrace is None:
            b = None
        else:
            b = _SubRaceSeamstress(subrace).run(a)

        c = AnthropometricCalculator(race, sex, subrace)
        height, weight = c.calculate(True)
        a["height"] = height
        a["weight"] = weight

        super(DataSet, self).__init__()
        self.parse_dataset(a, b)
        self.data = self.read_dataset(True)


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
