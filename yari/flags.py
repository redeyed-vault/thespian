from abc import ABC, abstractmethod
from collections import namedtuple

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
        del self.dataset["flags"]

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

        del self.dataset["flags"]

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
        # Set base ancestry
        base_ancestry_options = self.dataset.get("ancestry")
        if len(base_ancestry_options) == 0:
            self.dataset["ancestry"] = None
        else:
            ancestry = prompt("What is your draconic ancestry?", base_ancestry_options)
            self.dataset["ancestry"] = ancestry
            self.dataset["resistances"] = [self.dataset.get("resistances").get(ancestry)]
            _e(f"INFO: You set your draconic ancestry to > {ancestry}.", "green")

        # Set base languages
        base_languages = list()
        for language in self.dataset.get("languages"):
            if type(language) is list:
                base_languages += language
                self.dataset["languages"].remove(language)

        # Set base spells
        # base_spells = list()
        base_spell_options = self.dataset.get("spells")
        if len(base_spell_options) != 0:
            if type(base_spell_options) is dict:
                caster_level = int(prompt("What is your caster level?", list(range(1, 21))))
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

        del self.dataset["flags"]

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
                        f"INFO: You chose the '{proficiency}'' proficiency > {choice}.",
                        "green",
                    )
                self.dataset[proficiency] = base_skills

        return self.dataset

    def run(self):
        return self._honor_flags()


class SubRaceSeamstress(_FlagSeamstress):
    def __init__(self, query_id):
        super(SubRaceSeamstress, self).__init__(
            "subraces", query_id, ("language", "spell")
        )

    def _honor_flags(self, omitted_values=None):
        for flag in self.allowed_flags:
            if flag not in self.flags:
                continue
            dataset_value = self.dataset.get(flag)
            if type(dataset_value) is list:
                flag_value = self.flags.get(flag)
                for _ in range(flag_value):
                    options = [
                        x
                        for x in dataset_value
                        if x not in self.dataset.get(flag + "s")
                    ]
                    bonus_language = prompt(
                        f"Choose bonus '{flag}' ({flag_value}):", options
                    )
                    self.dataset[flag + "s"].append(bonus_language)
                    _e(
                        f"INFO: You chose a '{flag}' bonus > {bonus_language}.",
                        "green",
                    )

        del self.dataset["flags"]
        del self.dataset["spell"]

        return self.dataset

    def run(self, omitted_values=None):
        return self._honor_flags(omitted_values)


class ClassSeamstress:
    def __init__(self, klass, omitted_values=None):
        a = _BaseClassSeamstress(klass).run(omitted_values)
        b = _SubClassSeamstress(a.get("subclass"), a.get("level")).run(omitted_values)
        print(Dataset(a, b).dataset)


class RaceSeamstress:
    def __init__(self, race):
        a = _BaseRaceSeamstress(race).run()
        b = None
        #b = _SubClassSeamstress(a.get("subclass"), a.get("level")).run(omitted_values)
        print(Dataset(a, b).dataset)


class Dataset:
    def __init__(self, a, b=None):
        if type(b) is dict:
            for key, value in b.items():
                if key not in a:
                    a[key] = value
                    continue
                if type(value) is dict:
                    a_dict = a.get(key)
                    for subkey, subvalue in value.items():
                        if subkey not in a_dict:
                            a[key][subkey] = subvalue
                        else:
                            a[key][subkey] = a_dict.get(subkey) + subvalue
                    continue
                if type(value) is list:
                    a_list = a.get(key)
                    if type(a_list) is list:
                        a[key] = a_list + value

        self.dataset = a
        keywords = list(self.dataset.keys())
        keywords.sort()
        sorted_dataset = {}
        for keyword in keywords:
            if keyword in self.dataset:
                sorted_dataset[keyword] = self.dataset.get(keyword)
        dataset = namedtuple("Dataset", keywords)
        self.dataset = dataset(**sorted_dataset)


a = RaceSeamstress("Firbolg")

# omit_values = {"languages": ["Giant"], "skills": ["Persuasion"]}
# b = ClassSeamstress("Bard", omit_values)
