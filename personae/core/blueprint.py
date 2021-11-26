from abc import ABC, abstractmethod

from .errors import BlueprintError
from .sources import Load
from .utils import _ok, prompt

LEVEL_RANGE = list(range(1, 21))


class _Blueprint(ABC):
    """Generates basic DnD character blueprint."""

    def __init__(self, db, query_id, allowed_flags):
        guidelines = Load.get_columns(query_id, source_file=db)
        if guidelines is None:
            raise BlueprintError(
                f"Blueprint guides could not be found for '{query_id}'."
            )

        self.allowed_flags = allowed_flags
        self.blueprint = guidelines
        self.guides = self._draw(self.blueprint)

    def _draw(self, bp):
        if "guides" not in bp or bp.get("guides") == "none":
            return None

        blueprint = dict()
        for guide in bp.get("guides").split("|"):
            if "," not in guide:
                raise BlueprintError("Each guide entry must include a comma.")

            guide_pair = guide.split(",")
            if len(guide_pair) != 2:
                raise BlueprintError("Each guide must be a pair (two values only).")

            (guide_name, guide_value) = guide_pair

            if "&&" in guide_name:
                guide_options = guide_name.split("&&")
                if len(guide_options) > 1:
                    guide_name = prompt("Choose your guides:", guide_options)
                    guide_options.remove(guide_name)
                    for option in guide_options:
                        if option in self.blueprint:
                            self.blueprint[option] = []

                    _ok(f"You chose the '{guide_name}' guide.")
                else:
                    raise BlueprintError(
                        "If a guide has multiple options available, it must have two or more options."
                    )

            blueprint[guide_name] = int(guide_value)

        return blueprint

    @abstractmethod
    def _read(self):
        pass

    @abstractmethod
    def run(self):
        pass


class BaseClassBlueprint(_Blueprint):
    """Generates base class blueprints."""

    def __init__(self, klass):
        super(BaseClassBlueprint, self).__init__(
            "classes", klass, ("ability", "skills", "subclass", "tools")
        )

        # Set base character level.
        level = int(prompt("Choose your class level:", LEVEL_RANGE))
        self.blueprint["level"] = level
        _ok(f"Level set to >> {level}.")

        # Set a dictonary of class features by level.
        self.blueprint["features"] = {
            x: y for x, y in self.blueprint.get("features").items() if x <= level
        }

        # Set base proficiency bonus.
        from math import ceil

        self.blueprint["proficiency"] = ceil((level / 4) + 1)

        # Set base hit die/points.
        hit_die = int(self.blueprint.get("hit_die"))
        self.blueprint["hit_die"] = f"{level}d{hit_die}"
        self.blueprint["hp"] = hit_die
        if level > 1:
            new_level = level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            self.blueprint["hp"] += sum(die_rolls)

        # Set base spellslots.
        try:
            self.blueprint["spellslots"] = self.blueprint.get("spellslots").get(level)
        except AttributeError:
            self.blueprint["spellslots"] = dict()

        # Set other base values.
        self.blueprint["bonusmagic"] = None
        self.blueprint["klass"] = klass
        self.blueprint["feats"] = list()

    def _read(self, omitted_values=None):
        for flag in self.allowed_flags:
            # Halt if no flags specified.
            if self.guides is None:
                break

            # Skip if specified flag is not defined.
            if flag not in self.guides:
                continue

            # Ignore subclass selection if character is < 3rd level.
            if self.blueprint.get("level") < 3 and flag == "subclass":
                self.blueprint["subclass"] = None
                continue

            # Set primary class ability, if applicable.
            if flag == "ability":
                for rank, abilities in self.blueprint.get(flag).items():
                    if not isinstance(abilities, list):
                        continue

                    ability_selection = prompt(f"Choose a primary ability:", abilities)
                    self.blueprint[flag][rank] = ability_selection
                    _ok(f"Primary ability '{ability_selection}' selected.")

                self.blueprint[flag] = tuple(self.blueprint[flag].values())
                continue

            num_of_instances = self.guides.get(flag)
            flag_options = self.blueprint.get(flag)
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
                    self.blueprint[flag] = option_selections + omitted_values
                else:
                    self.blueprint[flag] = option_selections

        ability = self.blueprint.get("ability")
        if isinstance(ability, dict):
            self.blueprint["ability"] = tuple(ability.values())

        return self.blueprint

    def run(self, omitted_values=None):
        return self._read(omitted_values)


class SubClassBlueprint(_Blueprint):
    """Generates base subclass blueprints."""

    def __init__(self, subclass, level=1):
        super(SubClassBlueprint, self).__init__(
            "subclasses", subclass, ("languages", "skills")
        )
        self.blueprint["features"] = {
            x: y for x, y in self.blueprint.get("features").items() if x <= level
        }

    def _read(self, omitted_values=None):
        for flag in self.allowed_flags:
            if self.guides is None:
                break

            if flag not in self.guides:
                continue

            bonus_selections = list()
            num_of_instances = self.guides.get(flag)
            _ok(f"Allotted bonus total for '{flag}': {num_of_instances}")
            for _ in range(num_of_instances):
                bonus_choice = prompt(
                    f"Choose a bonus from the '{flag}' selection list:",
                    self.blueprint.get(flag),
                    omitted_values.get(flag),
                )
                bonus_selections.append(bonus_choice)
                _ok(f"Bonus '{bonus_choice}' selected from '{flag}' list.")

            if len(bonus_selections) > 0:
                self.blueprint[flag] = bonus_selections

        return self.blueprint

    def run(self, omitted_values=None):
        return self._read(omitted_values)


class BaseRaceBlueprint(_Blueprint):
    """Generates base race blueprints."""

    def __init__(self, race):
        super(BaseRaceBlueprint, self).__init__(
            "races",
            race,
            ("armors", "languages", "skills", "subrace", "tools", "weapons"),
        )
        self._race = self.blueprint["race"] = race
        # self.tapestry["race"] = race

    def _read(self):
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
        self.blueprint["alignment"] = alignment
        _ok(f"Alignment set to >> {alignment}")

        # Set base ancestry, for Dragonborn characters.
        base_ancestry_options = self.blueprint.get("ancestry")
        if len(base_ancestry_options) == 0:
            self.blueprint["ancestry"] = None
        else:
            ancestry = prompt("Choose your draconic ancestry:", base_ancestry_options)
            self.blueprint["ancestry"] = ancestry
            self.blueprint["resistances"] = [self.blueprint.get("resistances").get(ancestry)]
            _ok(f"Draconic ancestry set to >> {ancestry}")

        # Set base background
        base_background_options = Load.get_columns(source_file="backgrounds")
        background = prompt("Choose your background:", base_background_options)
        self.blueprint["background"] = background
        _ok(f"Background set to >> {background}")

        # Set base languages
        base_language_options = self.blueprint.get("languages")
        actual_base_languages = list()
        for language in base_language_options:
            if isinstance(language, list):
                base_language_options.remove(language)
                actual_base_languages = language
                break

        self.blueprint["languages"] = actual_base_languages

        # Set additional base language, if applicable.
        # For HalfElf, Human, and Tabaxi characters.
        if len(base_language_options) != 0:
            additional_language = prompt(
                "Choose your additional language:", base_language_options
            )
            self.blueprint["languages"].append(additional_language)
            _ok(f"Added language >> {additional_language}")

        # Set base spells
        base_spell_options = self.blueprint.get("spells")
        if len(base_spell_options) != 0:
            if isinstance(base_spell_options, dict):
                caster_level = int(
                    prompt("Choose your spellcaster level:", LEVEL_RANGE)
                )
                base_spells = []
                for req_level, spell_list in base_spell_options.items():
                    if req_level <= caster_level:
                        base_spells += spell_list
                self.blueprint["spells"] = base_spells
                _ok(f"Caster level set to >> {caster_level}")

        # Set base subrace, if applicable
        base_subrace_options = self.blueprint.get("subrace")
        if len(base_subrace_options) > 0:
            subrace = prompt(
                f"Choose your '{self._race}' subrace:",
                base_subrace_options,
            )
            self.blueprint["subrace"] = subrace
            _ok(f"Subrace set to >> {subrace}")
        else:
            self.blueprint["subrace"] = None

        # No flags actually specified in configuration
        if self.guides is None:
            return self.blueprint

        # Determine bonus armors, skills, tools proficiencies
        for proficiency in ("armors", "skills", "tools", "weapons"):
            # If proficiency is not a specified flag, move on.
            if proficiency not in self.guides:
                continue

            proficiency_options = self.blueprint.get(proficiency)
            if len(proficiency_options) == 0:
                continue

            proficiency_selections = list()
            num_of_instances = self.guides.get(proficiency)
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
                self.blueprint[proficiency] = proficiency_selections

        return self.blueprint

    def run(self):
        return self._read()


class SubRaceBlueprint(_Blueprint):
    """Generates base subrace blueprints."""

    def __init__(self, subrace):
        super(SubRaceBlueprint, self).__init__(
            "subraces", subrace, ("language", "spell")
        )

    def _read(self, omitted_values=None):
        # No flags actually specified
        if self.guides is None:
            return self.blueprint

        # Set base spells
        base_spell_options = self.blueprint.get("spells")
        if len(base_spell_options) != 0:
            spell_selections = []

            # Spells in dictionary format do automatic selection.
            if isinstance(base_spell_options, dict):
                caster_level = int(prompt("Choose your caster level:", LEVEL_RANGE))
                for req_level, spell_list in base_spell_options.items():
                    if req_level <= caster_level:
                        spell_selections += spell_list
                self.blueprint["spells"] = spell_selections
                _ok(f"Caster level set to >> {caster_level}")

            # Spells in list format do manual selection.
            if isinstance(base_spell_options, list):
                if "spells" in self.guides:
                    num_of_instances = self.guides.get("spells")
                    for _ in range(num_of_instances):
                        spell_selection = prompt(
                            f"Choose your bonus spell:",
                            base_spell_options,
                            spell_selections,
                        )
                        spell_selections.append(spell_selection)
                        _ok(f"Added spell >> {spell_selection}")
                    self.blueprint["spells"] = spell_selections

        # Determine bonus languages, skills, proficiencies
        for proficiency in ("armors", "languages", "skills", "tools", "weapons"):
            # If proficiency not a specified flag, move on.
            if proficiency not in self.guides:
                continue

            proficiency_options = self.blueprint.get(proficiency)
            if len(proficiency_options) == 0:
                continue

            proficiency_selections = list()
            blacklisted_values = omitted_values.get(proficiency)
            if len(blacklisted_values) > 0:
                proficiency_selections += blacklisted_values

            num_of_instances = self.guides.get(proficiency)
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
                self.blueprint[proficiency] = proficiency_selections

        return self.blueprint

    def run(self, omitted_values=None):
        return self._read(omitted_values)
