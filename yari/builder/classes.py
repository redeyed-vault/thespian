from random import choice, sample

from yari._errors import Error
from .._utils import (
    get_all_languages,
    get_is_background,
    get_is_class,
    get_is_subclass,
    get_language_by_class,
    get_proficiency_bonus,
    get_skills_by_subclass,
    prompt,
)
from yari.builder._yaml import Load


class ClassBuilder:
    def __init__(
        self,
        klass: str,
        subclass: str,
        skills: list,
        level: int = 1,
        background: str = "",
    ) -> None:
        # Class is not valid
        if not get_is_class(klass):
            raise Error(f"Invalid class option specified '{klass}'.")

        # Subclass is not valid
        if not get_is_subclass(subclass, klass):
            raise Error(f"Subclass '{subclass}' is not a valid option for '{klass}'.")

        # If level is not integer
        if not isinstance(level, int):
            raise Error("Invalid type specified. 'level' must be of type 'int'.")

        # If level is between 1-20
        if level not in range(1, 21):
            raise Error("Argument 'level' value must be between 1-20.")

        # Unset subclass if character is below level 3
        if level < 3:
            subclass = ""

        # If background set, make sure its valid
        if background != "" and not get_is_background(background):
            raise Error(f"Character background '{background}' is invalid.")

        # Skills parameter can only be of type list
        if not isinstance(skills, list):
            raise Error("Argument 'race_skills' value must be a 'list'.")

        # Get default class template
        self.klass = klass
        class_data = Load.get_columns(klass, source_file="classes")
        if class_data is None:
            raise Error(f"Cannot load class template for '{self.klass}'.")

        # Assign default values
        self.subclass = subclass
        self.level = level
        self.abilities = class_data.get("abilities")
        self.background = class_data.get("background")
        self.equipment = class_data.get("equipment")
        self.features = class_data.get("features")
        self.hitdie = class_data.get("hit_die")
        self.hitpoints = None
        self.proficiency_bonus = None
        self.languages = class_data.get("languages")
        self.armors = class_data.get("proficiency").get("armors")
        self.tools = class_data.get("proficiency").get("tools")
        self.weapons = class_data.get("proficiency").get("weapons")
        self.saving_throws = class_data.get("saving_throws")
        self.bonusmagic = None
        self.spell_slots = class_data.get("spell_slots")
        self.subclasses = class_data.get("subclasses")

        # Exclude from class skills any skills already possessed (if applicable)
        if len(skills) > 0:
            self.skills = [x for x in skills if x not in class_data.get("skills")]
        else:
            self.skills = class_data.get("skills")

    def __repr__(self):
        if self.subclass != "None":
            return '<{} class="{}" subclass="{}" level="{}">'.format(
                self.__class__.__name__, self.klass, self.subclass, self.level
            )
        else:
            return '<{} class="{}" level="{}">'.format(
                self.__class__.__name__, self.klass, self.level
            )

    def _add_proficiencies(self) -> None:
        """
        Merge class proficiencies with subclass proficiencies (if applicable).

            - Add proficiencies
            - Add languages
            - Add skills

        """
        # Proficiencies
        # Get starting armor, tool and weapon proficiencies
        def assign_base_proficiency(
            proficiency_category, proficiency_list, sample_int=None
        ):
            if isinstance(sample_int, int):
                proficiency_list = sample(proficiency_list, sample_int)

            if proficiency_category == "armors":
                self.armors = proficiency_list
            elif proficiency_category == "tools":
                self.tools = proficiency_list
            elif proficiency_category == "weapons":
                self.weapons = proficiency_list

        for category in (
            "armors",
            "tools",
            "weapons",
        ):
            base_proficiency = Load.get_columns(
                self.klass, "proficiency", category, source_file="classes"
            )

            # Generate sample count if proficiency has random selection
            # i.e: Monk gets one random tool proficiency
            if len(base_proficiency) < 2:
                sample_count = None
            else:
                sample_count = base_proficiency[-1]
                if not isinstance(sample_count, int):
                    sample_count = None

            if sample_count is None:
                assign_base_proficiency(category, base_proficiency)
            elif isinstance(sample_count, int):
                del base_proficiency[-1]
                sample_count = int(sample_count)
                assign_base_proficiency(category, base_proficiency, sample_count)

        # If subclass specified
        # Check if subclass proficiencies available
        # Look through proficiency categories and upgrade lists as necessary
        # Remove all proficiencies from bonus proficiency list
        # If already possessed by the character
        # Add bonus proficiency to the appropriate category
        if self.subclass != "None":
            # Get the subclass proficiency categories
            subclass_proficiency_categories = Load.get_columns(
                self.subclass, "proficiency", source_file="subclasses"
            )
            # Subclass has proficiencies available
            if subclass_proficiency_categories is not None:
                for category in tuple(subclass_proficiency_categories.keys()):
                    # Get specific subclass proficiencies by category
                    subclass_proficiencies = Load.get_columns(
                        self.subclass, "proficiency", category, source_file="subclasses"
                    )
                    # Cycle through bonus proficiencies, then add by category
                    for proficiency in subclass_proficiencies:
                        if category == "armors":
                            if proficiency not in self.armors:
                                self.armors.append(proficiency)
                        elif category == "tools":
                            if proficiency not in self.tools:
                                self.tools.append(proficiency)
                        elif category == "weapons":
                            if proficiency not in self.weapons:
                                self.weapons.append(proficiency)
                        else:
                            raise ValueError(
                                f"Invalid proficiency category '{category}'"
                            )

        # Languages
        # Add bonus class specific languages, (if applicable)
        bonus_languages = get_language_by_class(self.klass)
        if len(bonus_languages) != 0:
            bonus_language = bonus_languages[0]
            if bonus_language not in self.languages:
                self.languages.append(bonus_languages)

        # Skills
        # Set the skill groundwork.
        skill_pool = self.skills
        skills = list()

        # Determine skill allotment by class.
        if self.klass in ("Rogue",):
            allotment = 4
        elif self.klass in ("Bard", "Ranger"):
            allotment = 3
        else:
            allotment = 2

        # Select class skills based on starting count generated above
        # Add class skills to skill list
        skills = skills + sample(skill_pool, allotment)

        # Add subclass bonus skills at level 3 or above, (if applicable)
        if self.level >= 3:
            bonus_skills = get_skills_by_subclass(self.subclass)
            if bonus_skills is not None:
                if len(bonus_skills) == 1:
                    skills.append(bonus_skills[0])
                else:
                    # College of Lore - 3 bonus skills
                    # Samurai - 1 bonus language or skill
                    # Otherwise - 1 bonus skill
                    bonus_skills = [x for x in bonus_skills if x not in skills]
                    if self.subclass == "College of Lore":
                        skills = skills + sample(bonus_skills, 3)
                    elif self.subclass == "Samurai":
                        bonus_choice = choice(("Language", "Skill"))
                        if bonus_choice == "Language":
                            samurai_language = [
                                x
                                for x in get_all_languages()
                                if x not in self.languages
                            ]
                            self.languages = self.languages + sample(
                                samurai_language, 1
                            )
                        else:
                            skills = skills + sample(bonus_skills, 1)
                    else:
                        skills = skills + sample(bonus_skills, 1)

        skills.sort()
        self.skills = skills

        # Proficiency handling and allotment (if applicable).
        self.proficiency_bonus = get_proficiency_bonus(self.level)

    def _add_spell_slots(self):
        """
        Generates character's spell slots.

        """
        # Character has no spell slots
        # Or character is a Fighter/Rogue and not Eldritch Knight/Arcane Trickster
        # Otherwise character has spellcasting ability
        if (
            self.spell_slots is None
            or self.klass in ("Fighter", "Rogue")
            and self.subclass
            not in (
                "Arcane Trickster",
                "Eldritch Knight",
            )
        ):
            self.spell_slots = "0"
        else:
            self.spell_slots = self.spell_slots.get(self.level)

    def run(self) -> None:
        """Generates character's class specifics."""
        for index, ability_options in self.abilities.items():
            if isinstance(ability_options, list):
                ability_option_list = "\n".join(ability_options)
                message = f"Choose your primary ability:\n\n{ability_option_list}\n\n>"
                chosen_ability = prompt(message, ability_options)
                self.abilities[index] = chosen_ability

        class_equipment = Load.get_columns(
            self.klass, "equipment", source_file="classes"
        )
        background_equipment = Load.get_columns(
            self.background, "equipment", source_file="backgrounds"
        )
        equipment = class_equipment + background_equipment
        self.equipment = equipment

        # Truncate base class features by level
        self.features = {x: y for (x, y) in self.features.items() if x <= self.level}

        # Merge class and subclass features by level (if applicable)
        if self.subclass != "":
            subclass_features = Load.get_columns(
                self.subclass, "features", source_file="subclasses"
            )
            for level_obtained, _ in subclass_features.items():
                # Stop if feature is too high level for character
                if level_obtained > self.level:
                    break

                # If features already assigned for this level
                # Append subclass features to class features
                # Otherwise make new listing for level with associated features
                if level_obtained in self.features:
                    feature_list = (
                        self.features[level_obtained]
                        + subclass_features[level_obtained]
                    )
                    feature_list.sort()
                    self.features[level_obtained] = feature_list
                else:
                    self.features[level_obtained] = subclass_features[level_obtained]

        # Convert each feature list by level to a tuple
        self.features = {l: tuple(f) for (l, f) in self.features.items()}

        # Calculate hit die/points
        hit_die = int(self.hitdie)
        self.hitdie = f"{self.level}d{hit_die}"
        self.hitpoints = hit_die
        if self.level > 1:
            new_level = self.level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            self.hitpoints += sum(die_rolls)

        # Adds extended magic spells (Domain, Warlock, etc)."""
        if self.subclass == "":
            self.bonusmagic = {}
        else:
            self.bonusmagic = Load.get_columns(
                self.subclass, "bonusmagic", source_file="subclasses"
            )
            self.bonusmagic = {
                x: y for (x, y) in self.bonusmagic.items() if x <= self.level
            }
            extended_magic_list = list()
            for _, spells in self.bonusmagic.items():
                for spell in spells:
                    extended_magic_list.append(spell)
            extended_magic_list.sort()
            self.bonusmagic = extended_magic_list

        self._add_proficiencies()
        self._add_spell_slots()
