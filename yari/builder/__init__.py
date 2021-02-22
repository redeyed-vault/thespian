from random import sample

from .errors import Error
from .._dice import roll
from .._utils import (
    get_is_background,
    get_is_class,
    get_is_race,
    get_is_subclass,
    get_language_by_class,
    get_proficiency_bonus,
    get_subraces_by_race,
    has_subraces,
    prompt,
)
from .._yaml import Load


class YariBuilder:
    def __init__(
        self,
        race: str,
        subrace: str,
        klass: str,
        subclass: str,
        level: int = 1,
        sex: str = "Female",
        background: str = "",
    ):
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

        if not get_is_class(klass):
            raise Error(f"Invalid class option specified '{klass}'.")

        if not get_is_subclass(subclass, klass):
            raise Error(f"Subclass '{subclass}' is not a valid option for '{klass}'.")

        if sex not in (
            "Female",
            "Male",
        ):
            raise Error(f"Value '{sex}' is not a valid gender option.")

        if background != "" and not get_is_background(background):
            raise Error(f"Character background '{background}' is invalid.")

        if isinstance(level, int):
            if not range(1, 21):
                raise Error("Value 'level' must be between 1-20.")
        else:
            raise Error("Value must be of type 'integer'.")

        if level < 3:
            subclass = ""

        race_data = Load.get_columns(race, source_file="races")
        if race_data is None:
            raise Error(f"Cannot load race template for '{race}'.")

        racial_proficiencies = race_data.get("proficiency")
        for category in racial_proficiencies:
            base_proficiencies = racial_proficiencies.get(category)
            if len(base_proficiencies) >= 2:
                last_value = base_proficiencies[-1]
                if isinstance(last_value, int):
                    del base_proficiencies[-1]
                    base_proficiencies = sample(base_proficiencies, last_value)
            race_data["proficiency"][category] = base_proficiencies

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
                    if (
                        subrace_darkvision is not None
                        and subrace_darkvision > race_darkvision
                    ):
                        race_data[trait] = subrace_darkvision
                elif trait == "innatemagic":
                    if race_data[trait] is None and subrace_data[trait] is None:
                        race_data[trait] = list()
                        continue
                    else:
                        if race_data[trait] is None and subrace_data[trait] is not None:
                            race_data[trait] = subrace_data[trait]
                        innate_spells = race_data[trait]
                        if len(innate_spells) == 0:
                            continue
                        if isinstance(innate_spells, list):
                            if len(innate_spells) >= 2:
                                last_value = innate_spells[-1]
                                if isinstance(last_value, int):
                                    del innate_spells[-1]
                                    race_data[trait] = sample(innate_spells, last_value)
                        elif isinstance(innate_spells, dict):
                            spell_list = list()
                            innate_spells = {
                                x: y
                                for (x, y) in race_data[trait].items()
                                if x <= level
                            }
                            for _, spells in innate_spells.items():
                                for spell in spells:
                                    spell_list.append(spell)
                            race_data[trait] = spell_list
                elif trait == "languages":
                    race_data[trait] += subrace_data[trait]
                elif trait == "proficiency":
                    subrace_proficiency_types = subrace_data[trait]
                    for category in tuple(subrace_proficiency_types.keys()):
                        subrace_proficiencies = subrace_proficiency_types.get(category)
                        race_data[trait][category] += subrace_proficiencies
                elif trait == "skills":
                    race_data[trait] += subrace_data[trait]
                elif trait == "ratio":
                    if race_data[trait] is None:
                        subrace_ratio = subrace_data[trait]
                        race_data[trait] = subrace_ratio
                elif trait == "resistances":
                    race_data[trait] += subrace_data[trait]
                elif trait == "traits":
                    for other in subrace_data.get(trait):
                        race_data[trait].append(other)

            for category in (
                "armors",
                "tools",
                "weapons",
            ):
                base_proficiency_list = Load.get_columns(
                    klass, "proficiency", category, source_file="classes"
                )
                if len(base_proficiency_list) < 2:
                    sample_count = None
                else:
                    sample_count = base_proficiency_list[-1]
                    if not isinstance(sample_count, int):
                        sample_count = None
                base_proficiency_category = race_data["proficiency"][category]
                if sample_count is None:
                    base_proficiency_list = [
                        x
                        for x in base_proficiency_list
                        if x not in race_data["proficiency"][category]
                    ]
                    base_proficiency_category += base_proficiency_list
                elif isinstance(sample_count, int):
                    del base_proficiency_list[-1]
                    base_proficiency_list = [
                        x
                        for x in base_proficiency_list
                        if x not in race_data["proficiency"][category]
                    ]
                    sample_count = int(sample_count)
                    base_proficiency_category += sample(
                        base_proficiency_list, sample_count
                    )

            if subclass != "":
                subclass_proficiency_categories = Load.get_columns(
                    subclass, "proficiency", source_file="subclasses"
                )
                if subclass_proficiency_categories is not None:
                    for category in tuple(subclass_proficiency_categories.keys()):
                        subclass_proficiencies = Load.get_columns(
                            subclass, "proficiency", category, source_file="subclasses"
                        )
                        proficiency_base = race_data["proficiency"][category]
                        for proficiency in subclass_proficiencies:
                            if proficiency not in proficiency_base:
                                proficiency_base.append(proficiency)

            bonus_languages = get_language_by_class(klass)
            if len(bonus_languages) != 0:
                bonus_language = bonus_languages[0]
                if bonus_language not in race_data["languages"]:
                    race_data["languages"].append(bonus_languages)

        # Calculate height/weight
        height_base = race_data.get("ratio").get("height").get("base")
        height_modifier = race_data.get("ratio").get("height").get("modifier")
        height_modifier = sum(list(roll(height_modifier)))
        weight_base = race_data.get("ratio").get("weight").get("base")
        weight_modifier = race_data.get("ratio").get("weight").get("modifier")
        weight_modifier = sum(list(roll(weight_modifier)))
        race_data["height"] = height_base + height_modifier
        race_data["weight"] = (height_modifier * weight_modifier) + weight_base
        del race_data["ratio"]

        class_data = Load.get_columns(klass, source_file="classes")
        if class_data is None:
            raise Error(f"Cannot load class template for '{klass}'.")

        skill_pool = class_data["skills"]
        skill_pool = [x for x in skill_pool if x not in race_data["skills"]]
        if klass in ("Rogue",):
            allotment = 4
        elif klass in ("Bard", "Ranger"):
            allotment = 3
        else:
            allotment = 2
        race_data["skills"] += sample(skill_pool, allotment)

        self.abilities = class_data.get("abilities")
        self.ancestor = None
        self.armors = race_data.get("proficiency").get("armors")
        self.background = class_data.get("background")
        self.bonus = race_data.get("bonus")
        self.bonusmagic = None
        self.darkvision = race_data.get("darkvision")
        self.equipment = class_data.get("equipment")
        self.features = class_data.get("features")
        self.height = race_data.get("height")
        self.hitdie = class_data.get("hit_die")
        self.hitpoints = None
        self.innatemagic = race_data.get("innatemagic")
        self.klass = klass
        self.languages = race_data.get("languages")
        self.level = level
        self.proficiency_bonus = get_proficiency_bonus(self.level)
        self.race = race
        self.resistances = race_data.get("resistances")
        self.savingthrows = class_data.get("saving_throws")
        self.sex = sex
        self.size = race_data.get("size")
        self.skills = race_data.get("skills")
        self.speed = race_data.get("speed")
        self.spell_slots = class_data.get("spell_slots")
        self.subclass = subclass
        self.subclasses = class_data.get("subclasses")
        self.subrace = subrace
        self.tools = race_data.get("proficiency").get("tools")
        self.traits = race_data.get("traits")
        self.weapons = race_data.get("proficiency").get("weapons")
        self.weight = race_data.get("weight")

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
