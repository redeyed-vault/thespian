from abc import ABC, abstractmethod
from collections import namedtuple

from .errors import Error
from .sources import Load
from .utils import _e, prompt


class _FlagSeamstress(ABC):
    def __init__(self, database, query_id, allowed_flags):
        result = Load.get_columns(query_id, source_file=database)
        if result is None:
            raise Error(f"Data could not be found for '{query_id}'.")

        self.allowed_flags = allowed_flags
        self.tapestry = result
        self.flags = self._sew_flags(self.tapestry)

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
                        if option in self.tapestry:
                            self.tapestry[option] = []
                    _e(f"INFO: You chose the flagging option '{flag_name}'", "green")
                else:
                    raise Error(
                        "If a flag has multiple options available, it must have two or more options."
                    )

            sewn_flags[flag_name] = int(flag_value)

        return sewn_flags

    @abstractmethod
    def run(self):
        pass


class _BaseClassSeamstress(_FlagSeamstress):
    def __init__(self, klass):
        super(_BaseClassSeamstress, self).__init__(
            "classes", klass, ("ability", "skills", "subclass", "tools")
        )
        # Set base character level and features
        level = int(prompt("What level are you?", list(range(1, 21))))
        self.tapestry["level"] = level
        self.tapestry["features"] = {
            x: y for x, y in self.tapestry.get("features").items() if x <= level
        }
        _e(f"INFO: Your character level has been set to {level}.", "green")

        from math import ceil

        self.tapestry["proficiency"] = ceil((level / 4) + 1)

        # Set base hit die/points
        hit_die = int(self.tapestry.get("hit_die"))
        self.tapestry["hit_die"] = f"{level}d{hit_die}"
        self.tapestry["hp"] = hit_die
        if level > 1:
            new_level = level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            self.tapestry["hp"] += sum(die_rolls)

        self.tapestry["bonusmagic"] = None
        self.tapestry["klass"] = klass
        self.tapestry["feats"] = list()
        self.tapestry["spellslots"] = self.tapestry.get("spellslots").get(level)

    def _honor_flags(self, omitted_values=None):
        for flag in self.allowed_flags:
            # _e(f"INFO: Checking for allowed flag '{flag}'...", "yellow")
            if self.flags is None:
                # _e("INFO: No flags specified. Halting flag checking...", "red")
                break
            if flag not in self.flags:
                # _e(f"INFO: Flag '{flag}' not specified. Skipping...", "yellow")
                continue

            # Ignore subclass if character less than 3rd level.
            if self.tapestry.get("level") < 3 and flag == "subclass":
                self.tapestry["subclass"] = None
                continue

            if flag == "ability":
                for rank, abilities in self.tapestry.get(flag).items():
                    if type(abilities) is not list:
                        continue
                    choice = prompt(f"Choose class option '{flag}':", abilities)
                    self.tapestry[flag][rank] = choice
                    _e(f"You chose the ability > '{choice}'", "green")
                self.tapestry[flag] = tuple(self.tapestry[flag].values())
            else:
                num_of_instances = self.flags.get(flag)
                flag_options = self.tapestry.get(flag)
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
                        self.tapestry[flag] = option_selections + omitted_values
                    else:
                        self.tapestry[flag] = option_selections

        ability = self.tapestry.get("ability")
        if type(ability) is dict:
            self.tapestry["ability"] = tuple(ability.values())

        return self.tapestry

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class _SubClassSeamstress(_FlagSeamstress):
    def __init__(self, subclass, level=1):
        super(_SubClassSeamstress, self).__init__(
            "subclasses", subclass, ("languages", "skills")
        )
        self.tapestry["features"] = {
            x: y for x, y in self.tapestry.get("features").items() if x <= level
        }

    def _honor_flags(self, omitted_values=None):
        for flag in self.allowed_flags:
            if self.flags is None:
                break
            if flag not in self.flags:
                continue

            bonus_choices = list()
            bonus_options = self.tapestry.get(flag)
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
                    self.tapestry[flag] = bonus_choices

        return self.tapestry

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
        self.tapestry["race"] = race

    def _honor_flags(self):
        # Set alignment
        base_alignment_options = (
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
        self.tapestry["alignment"] = alignment
        _e(f"INFO: You set your alignment to > {alignment}.", "green")

        # Set base ancestry, for Dragonborn characters.
        base_ancestry_options = self.tapestry.get("ancestry")
        if len(base_ancestry_options) == 0:
            self.tapestry["ancestry"] = None
        else:
            ancestry = prompt("What is your draconic ancestry?", base_ancestry_options)
            self.tapestry["ancestry"] = ancestry
            self.tapestry["resistances"] = [
                self.tapestry.get("resistances").get(ancestry)
            ]
            _e(f"INFO: You set your draconic ancestry to > {ancestry}.", "green")

        # Set base background
        base_background_options = Load.get_columns(source_file="backgrounds")
        background = prompt("What is your background?", base_background_options)
        self.tapestry["background"] = background
        _e(f"INFO: Character background '{background}' chosen.", "green")

        # Set base languages
        base_language_options = self.tapestry.get("languages")
        actual_base_languages = list()
        for language in base_language_options:
            if type(language) is list:
                base_language_options.remove(language)
                actual_base_languages = language
                break

        self.tapestry["languages"] = actual_base_languages

        # Set additional base language, if applicable.
        # For HalfElf, Human, and Tabaxi characters.
        if len(base_language_options) != 0:
            additional_language = prompt(
                "What additional language do you want?", base_language_options
            )
            self.tapestry["languages"].append(additional_language)
            _e(f"INFO: Character language '{additional_language}' chosen.", "green")

        # Set base spells
        base_spell_options = self.tapestry.get("spells")
        if len(base_spell_options) != 0:
            if type(base_spell_options) is dict:
                caster_level = int(
                    prompt("What is your caster level?", list(range(1, 21)))
                )
                base_spells = []
                for req_level, spell_list in base_spell_options.items():
                    if req_level <= caster_level:
                        base_spells += spell_list
                self.tapestry["spells"] = base_spells
                _e(f"INFO: You set your caster level to > {caster_level}.", "green")

        # Set base subrace, if applicable
        base_subrace_options = self.tapestry.get("subrace")
        if len(base_subrace_options) == 0:
            self.tapestry["subrace"] = None
        else:
            subrace = prompt("Choose your 'subrace'", base_subrace_options)
            self.tapestry["subrace"] = subrace
            _e(f"INFO: You set your subrace to > {subrace}.", "green")

        # No flags actually specified in configuration
        if self.flags is None:
            return self.tapestry

        # Determine bonus armors, skills, tools proficiencies
        for proficiency in ("armors", "skills", "tools", "weapons"):
            if proficiency not in self.flags:
                continue
            base_skills = list()
            base_skill_options = self.tapestry.get(proficiency)
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
                self.tapestry[proficiency] = base_skills

        return self.tapestry

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
            return self.tapestry

        # Set base spells
        base_spell_options = self.tapestry.get("spells")
        if len(base_spell_options) != 0:
            base_spells = []
            if type(base_spell_options) is dict:
                caster_level = int(
                    prompt("What is your caster level?", list(range(1, 21)))
                )
                for req_level, spell_list in base_spell_options.items():
                    if req_level <= caster_level:
                        base_spells += spell_list
                self.tapestry["spells"] = base_spells
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
                    self.tapestry["spells"] = base_spells

        # Determine bonus languages, skills, proficiencies
        for proficiency in ("armors", "languages", "skills", "tools", "weapons"):
            if proficiency not in self.flags:
                continue
            base_skills = list()
            base_skill_options = self.tapestry.get(proficiency)
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
                self.tapestry[proficiency] = base_skills

        return self.tapestry

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class MyTapestry:
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
        if type(a) is not dict:
            raise Error("First parameter must be of type 'dict'.")
        if type(b) is not dict and b is not None:
            raise Error("Second parameter must be of type 'dict' or 'NoneType'.")

        # Remove flags index, if applicable
        if "flags" in a:
            del a["flags"]
        if type(b) is dict and "flags" in b:
            del b["flags"]

        # Merge a and b dictionaries, if applicable.
        if type(b) is dict:
            for key, value in b.items():
                # If index not availble in root dictionary.
                if key not in a:
                    a[key] = value
                    continue
                # Merge dicts
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
                # Merge integers
                if type(value) is int:
                    a_int = a.get(key)
                    if type(a_int) is not int:
                        continue
                    if value > a_int:
                        a[key] = value
                # Merge lists
                if type(value) is list:
                    a_list = a.get(key)
                    if type(a_list) is list:
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


class ClassSeamstress(MyTapestry):
    def __init__(self, klass, omitted_values=None):
        a = _BaseClassSeamstress(klass).run(omitted_values)
        b = None
        subclass = a.get("subclass")
        if subclass is not None:
            b = _SubClassSeamstress(subclass, a.get("level")).run(omitted_values)

        super().__init__()
        self.weave(a, b)
        self.data = self.view(True)


class RaceSeamstress(MyTapestry):
    def __init__(self, race, sex):
        a = _BaseRaceSeamstress(race).run()
        subrace = a.get("subrace")
        if type(subrace) is not str or subrace == "":
            b = None
        else:
            b = _SubRaceSeamstress(subrace).run(a)

        from .metrics import AnthropometricCalculator

        c = AnthropometricCalculator(race, sex, subrace)
        height, weight = c.calculate(True)
        a["height"] = height
        a["weight"] = weight
        a["sex"] = sex

        super().__init__()
        self.weave(a, b)
        self.data = self.view(True)
