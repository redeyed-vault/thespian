from abc import ABC, abstractmethod
from collections import namedtuple

from .errors import SeamstressError
from .sources import Load
from .utils import _ok, prompt

LEVEL_RANGE = list(range(1, 21))


class _Seamstress(ABC):
    def __init__(self, database, query_id, allowed_flags):
        result = Load.get_columns(query_id, source_file=database)
        if result is None:
            raise SeamstressError(f"Data could not be found for '{query_id}'.")

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
                raise SeamstressError("Each flag entry must include a comma.")

            flag_pair = flag.split(",")
            if len(flag_pair) != 2:
                raise SeamstressError("Each flag must be a pair (two values only).")

            (flag_name, flag_value) = flag_pair

            if "&&" in flag_name:
                flag_options = flag_name.split("&&")
                if len(flag_options) > 1:
                    flag_name = prompt("Choose your flag option.", flag_options)
                    flag_options.remove(flag_name)
                    for option in flag_options:
                        if option in self.tapestry:
                            self.tapestry[option] = []
                    _ok(f"You chose the flagging option '{flag_name}'")
                else:
                    raise SeamstressError(
                        "If a flag has multiple options available, it must have two or more options."
                    )

            sewn_flags[flag_name] = int(flag_value)

        return sewn_flags

    @abstractmethod
    def run(self):
        pass


class _BaseClassSeamstress(_Seamstress):
    def __init__(self, klass):
        super(_BaseClassSeamstress, self).__init__(
            "classes", klass, ("ability", "skills", "subclass", "tools")
        )

        # Set base character level.
        level = int(prompt("Choose your class level:", LEVEL_RANGE))
        self.tapestry["level"] = level
        _ok(f"Level set to >> {level}.")

        # Set a dictonary of class features by level.
        self.tapestry["features"] = {
            x: y for x, y in self.tapestry.get("features").items() if x <= level
        }

        # Set base proficiency bonus.
        from math import ceil

        self.tapestry["proficiency"] = ceil((level / 4) + 1)

        # Set base hit die/points.
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

        # Set base spellslots.
        try:
            self.tapestry["spellslots"] = self.tapestry.get("spellslots").get(level)
        except AttributeError:
            self.tapestry["spellslots"] = dict()

        # Set other base values.
        self.tapestry["bonusmagic"] = None
        self.tapestry["klass"] = klass
        self.tapestry["feats"] = list()

    def _honor_flags(self, omitted_values=None):
        for flag in self.allowed_flags:
            # Halt if no flags specified.
            if self.flags is None:
                break

            # Skip if specified flag is not defined.
            if flag not in self.flags:
                continue

            # Ignore subclass selection if character is < 3rd level.
            if self.tapestry.get("level") < 3 and flag == "subclass":
                self.tapestry["subclass"] = None
                continue

            # Set primary class ability, if applicable.
            if flag == "ability":
                for rank, abilities in self.tapestry.get(flag).items():
                    if not isinstance(abilities, list):
                        continue

                    ability_selection = prompt(f"Choose a primary ability:", abilities)
                    self.tapestry[flag][rank] = ability_selection
                    _ok(f"Primary ability '{ability_selection}' selected.")

                self.tapestry[flag] = tuple(self.tapestry[flag].values())
                continue

            num_of_instances = self.flags.get(flag)
            flag_options = self.tapestry.get(flag)
            if isinstance(flag_options, list):
                if isinstance(omitted_values, dict) and flag in omitted_values:
                    omitted_values = omitted_values.get(flag)
                    if not isinstance(omitted_values, list):
                        continue
                    flag_options = [x for x in flag_options if x not in omitted_values]

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
                    _ok(f"Value added >> {chosen_option}.")

                if (
                    isinstance(option_selections, list)
                    and isinstance(omitted_values, list)
                    and len(omitted_values) > 0
                ):
                    self.tapestry[flag] = option_selections + omitted_values
                else:
                    self.tapestry[flag] = option_selections

        ability = self.tapestry.get("ability")
        if isinstance(ability, dict):
            self.tapestry["ability"] = tuple(ability.values())

        return self.tapestry

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class _SubClassSeamstress(_Seamstress):
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

            bonus_selections = list()
            num_of_instances = self.flags.get(flag)
            _ok(f"Allotted bonus total for '{flag}': {num_of_instances}")
            for _ in range(num_of_instances):
                bonus_choice = prompt(
                    f"Choose a bonus from the '{flag}' selection list:",
                    self.tapestry.get(flag),
                    omitted_values.get(flag),
                )
                bonus_selections.append(bonus_choice)
                _ok(f"Bonus '{bonus_choice}' selected from '{flag}' list.")

            if len(bonus_selections) > 0:
                self.tapestry[flag] = bonus_selections

        return self.tapestry

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class _BaseRaceSeamstress(_Seamstress):
    def __init__(self, race):
        super(_BaseRaceSeamstress, self).__init__(
            "races",
            race,
            ("armors", "languages", "skills", "subrace", "tools", "weapons"),
        )
        self._race = self.tapestry["race"] = race
        # self.tapestry["race"] = race

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
        alignment = prompt("Choose your alignment:", base_alignment_options)
        self.tapestry["alignment"] = alignment
        _ok(f"Alignment set to >> {alignment}")

        # Set base ancestry, for Dragonborn characters.
        base_ancestry_options = self.tapestry.get("ancestry")
        if len(base_ancestry_options) == 0:
            self.tapestry["ancestry"] = None
        else:
            ancestry = prompt("Choose your draconic ancestry:", base_ancestry_options)
            self.tapestry["ancestry"] = ancestry
            self.tapestry["resistances"] = [
                self.tapestry.get("resistances").get(ancestry)
            ]
            _ok(f"Draconic ancestry set to >> {ancestry}")

        # Set base background
        base_background_options = Load.get_columns(source_file="backgrounds")
        background = prompt("Choose your background:", base_background_options)
        self.tapestry["background"] = background
        _ok(f"Background set to >> {background}")

        # Set base languages
        base_language_options = self.tapestry.get("languages")
        actual_base_languages = list()
        for language in base_language_options:
            if isinstance(language, list):
                base_language_options.remove(language)
                actual_base_languages = language
                break

        self.tapestry["languages"] = actual_base_languages

        # Set additional base language, if applicable.
        # For HalfElf, Human, and Tabaxi characters.
        if len(base_language_options) != 0:
            additional_language = prompt(
                "Choose your additional language:", base_language_options
            )
            self.tapestry["languages"].append(additional_language)
            _ok(f"Added language >> {additional_language}")

        # Set base spells
        base_spell_options = self.tapestry.get("spells")
        if len(base_spell_options) != 0:
            if isinstance(base_spell_options, dict):
                caster_level = int(
                    prompt("Choose your spellcaster level:", LEVEL_RANGE)
                )
                base_spells = []
                for req_level, spell_list in base_spell_options.items():
                    if req_level <= caster_level:
                        base_spells += spell_list
                self.tapestry["spells"] = base_spells
                _ok(f"Caster level set to >> {caster_level}")

        # Set base subrace, if applicable
        base_subrace_options = self.tapestry.get("subrace")
        if len(base_subrace_options) > 0:
            subrace = prompt(
                f"Choose your '{self._race}' subrace:",
                base_subrace_options,
            )
            self.tapestry["subrace"] = subrace
            _ok(f"Subrace set to >> {subrace}")
        else:
            self.tapestry["subrace"] = None

        # No flags actually specified in configuration
        if self.flags is None:
            return self.tapestry

        # Determine bonus armors, skills, tools proficiencies
        for proficiency in ("armors", "skills", "tools", "weapons"):
            # If proficiency is not a specified flag, move on.
            if proficiency not in self.flags:
                continue

            proficiency_options = self.tapestry.get(proficiency)
            if len(proficiency_options) == 0:
                continue

            proficiency_selections = list()
            num_of_instances = self.flags.get(proficiency)
            _ok(
                f"Allotted bonus total for proficiency '{proficiency}': {num_of_instances}"
            )
            for _ in range(num_of_instances):
                proficiency_selection = prompt(
                    f"Choose your '{proficiency}' proficiency ({num_of_instances})",
                    proficiency_options,
                    proficiency_selections,
                )
                proficiency_selections.append(proficiency_selection)
                _ok(
                    f"Bonus '{proficiency_selection}' selected from '{proficiency}' list."
                )

            if len(proficiency_selections) > 0:
                self.tapestry[proficiency] = proficiency_selections

        return self.tapestry

    def run(self):
        return self._honor_flags()


class _SubRaceSeamstress(_Seamstress):
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
            spell_selections = []

            # Spells in dictionary format do automatic selection.
            if isinstance(base_spell_options, dict):
                caster_level = int(prompt("Choose your caster level:", LEVEL_RANGE))
                for req_level, spell_list in base_spell_options.items():
                    if req_level <= caster_level:
                        spell_selections += spell_list
                self.tapestry["spells"] = spell_selections
                _ok(f"Caster level set to >> {caster_level}")

            # Spells in list format do manual selection.
            if isinstance(base_spell_options, list):
                if "spells" in self.flags:
                    num_of_instances = self.flags.get("spells")
                    for _ in range(num_of_instances):
                        spell_selection = prompt(
                            f"Choose your bonus spell:",
                            base_spell_options,
                            spell_selections,
                        )
                        spell_selections.append(spell_selection)
                        _ok(f"Added spell >> {spell_selection}")
                    self.tapestry["spells"] = spell_selections

        # Determine bonus languages, skills, proficiencies
        for proficiency in ("armors", "languages", "skills", "tools", "weapons"):
            # If proficiency not a specified flag, move on.
            if proficiency not in self.flags:
                continue

            proficiency_options = self.tapestry.get(proficiency)
            if len(proficiency_options) == 0:
                continue

            proficiency_selections = list()
            blacklisted_values = omitted_values.get(proficiency)
            if len(blacklisted_values) > 0:
                proficiency_selections += blacklisted_values

            num_of_instances = self.flags.get(proficiency)
            _ok(
                f"Allotted bonus total for proficiency '{proficiency}': {num_of_instances}"
            )
            for _ in range(num_of_instances):
                proficiency_selection = prompt(
                    f"Choose a bonus from the '{proficiency}' proficiency list:",
                    proficiency_options,
                    proficiency_selections,
                )
                proficiency_selections.append(proficiency_selection)
                _ok(
                    f"Bonus '{proficiency_selection}' selected from '{proficiency}' list."
                )

            if len(proficiency_selections) > 0:
                self.tapestry[proficiency] = proficiency_selections

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
        if not isinstance(a, dict):
            raise Error("First parameter must be of type 'dict'.")
        if not isinstance(b, dict) and b is not None:
            raise Error("Second parameter must be of type 'dict' or 'NoneType'.")

        # Remove flags index, if applicable
        if "flags" in a:
            del a["flags"]
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
        if not isinstance(subrace, str) or subrace == "":
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
