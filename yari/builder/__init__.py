from random import sample

from ._yaml import Load
from .._errors import Error
from .._dice import roll
from .._utils import (
    get_language_by_class,
    get_proficiency_bonus,
    prompt,
)


class _YariBuilder:
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
        if level < 3:
            subclass = ""
        if background == "":
            background = Load.get_columns(klass, "background", source_file="classes")

        self.klass = klass
        self.level = level
        self.race = race
        self.sex = sex
        self.subclass = subclass
        self.subrace = subrace
        self.background = background

    @staticmethod
    def _truncate_dict(dict_to_truncate: dict, level_ceiling: int):
        return {x: y for (x, y) in dict_to_truncate.items() if x <= level_ceiling}

    def _build_class(self, klass, subclass, level, race_data):
        data = Load.get_columns(klass, source_file="classes")
        if data is None:
            raise Error(f"Cannot load class template for '{klass}'.")

        del data["subclasses"]

        for category in (
            "armors",
            "tools",
            "weapons",
        ):
            class_proficiency_list = data.get("proficiency").get(category)
            if len(class_proficiency_list) < 2:
                sample_count = None
            else:
                sample_count = class_proficiency_list[-1]
                if not isinstance(sample_count, int):
                    sample_count = None
            if sample_count is None:
                class_proficiency_list = [
                    x
                    for x in class_proficiency_list
                    if x not in race_data["proficiency"][category]
                ]
                data["proficiency"][category] = class_proficiency_list
            elif isinstance(sample_count, int):
                del class_proficiency_list[-1]
                class_proficiency_list = [
                    x
                    for x in class_proficiency_list
                    if x not in race_data["proficiency"][category]
                ]
                sample_count = int(sample_count)
                data["proficiency"][category] = sample(
                    class_proficiency_list, sample_count
                )

        bonus_languages = get_language_by_class(klass)
        if len(bonus_languages) != 0:
            bonus_language = bonus_languages[0]
            if bonus_language not in data["languages"]:
                data["languages"].append(bonus_languages)

        if (
            data["spellslots"] is None
            or self.klass in ("Fighter", "Rogue")
            and self.subclass
            not in (
                "Arcane Trickster",
                "Eldritch Knight",
            )
        ):
            data["spellslots"] = "0"
        else:
            data["spellslots"] = data["spellslots"].get(self.level)

        if subclass == "":
            data["features"] = self._truncate_dict(data["features"], level)
        else:
            subclass_data = Load.get_columns(subclass, source_file="subclasses")
            for feature, value in subclass_data.items():
                if feature == "bonusmagic":
                    if subclass_data[feature] is None:
                        data[feature] = list()
                        continue
                    bonus_magic = self._truncate_dict(subclass_data[feature], level)
                    extended_spell_list = list()
                    for spell_list in tuple(bonus_magic.values()):
                        extended_spell_list += spell_list
                    data[feature] = extended_spell_list
                elif feature == "features":
                    for level_obtained, feature_list in value.items():
                        if level_obtained in data["features"]:
                            data["features"][level_obtained] += feature_list
                        else:
                            data["features"][level_obtained] = feature_list
                    data["features"] = self._truncate_dict(data["features"], level)
                elif feature == "proficiency":
                    subclass_proficiency_categories = Load.get_columns(
                        subclass, feature, source_file="subclasses"
                    )
                    if subclass_proficiency_categories is not None:
                        for category in tuple(subclass_proficiency_categories.keys()):
                            subclass_proficiencies = Load.get_columns(
                                subclass,
                                "proficiency",
                                category,
                                source_file="subclasses",
                            )
                            proficiency_base = data["proficiency"][category]
                            for proficiency in subclass_proficiencies:
                                if proficiency not in proficiency_base:
                                    proficiency_base.append(proficiency)
                elif feature == "skills":
                    bonus_skills = subclass_data[feature]
                    if bonus_skills is None:
                        continue
                    if len(bonus_skills) == 1:
                        data[feature] += subclass_data[feature]

        # Calculate hit die/points
        hit_die = int(data["hit_die"])
        data["hitdie"] = f"{self.level}d{hit_die}"
        data["hitpoints"] = hit_die
        if self.level > 1:
            new_level = self.level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            data["hitpoints"] += sum(die_rolls)

        skill_pool = data["skills"]
        background_skills = Load.get_columns(
            self.background, "skills", source_file="backgrounds"
        )
        skill_pool = [
            x
            for x in skill_pool
            if x not in race_data["skills"] and x not in background_skills
        ]
        if klass in ("Rogue",):
            allotment = 4
        elif klass in ("Bard", "Ranger"):
            allotment = 3
        else:
            allotment = 2
        data["skills"] = background_skills
        data["skills"] += sample(skill_pool, allotment)

        return data

    def _build_race(self, race, subrace, level):
        data = Load.get_columns(race, source_file="races")
        if data is None:
            raise Error(f"Cannot load race template for '{race}'.")

        racial_proficiencies = data.get("proficiency")
        for category in racial_proficiencies:
            base_proficiencies = racial_proficiencies.get(category)
            if len(base_proficiencies) >= 2:
                last_value = base_proficiencies[-1]
                if isinstance(last_value, int):
                    del base_proficiencies[-1]
                    base_proficiencies = sample(base_proficiencies, last_value)
            data["proficiency"][category] = base_proficiencies

        if subrace != "":
            subrace_data = Load.get_columns(subrace, source_file="subraces")
            if subrace_data is None:
                raise Error(f"Cannot load subrace template for '{subrace}'.")
            for trait, value in subrace_data.items():
                if trait not in data:
                    data[trait] = subrace_data[trait]
                elif trait == "bonus":
                    for ability, bonus in value.items():
                        data[trait][ability] = bonus
                elif trait == "darkvision":
                    race_darkvision = data.get(trait)
                    subrace_darkvision = subrace_data.get(trait)
                    if (
                        subrace_darkvision is not None
                        and subrace_darkvision > race_darkvision
                    ):
                        data[trait] = subrace_darkvision
                elif trait == "innatemagic":
                    if data[trait] is None and subrace_data[trait] is None:
                        data[trait] = list()
                        continue
                    else:
                        if data[trait] is None and subrace_data[trait] is not None:
                            data[trait] = subrace_data[trait]
                        innate_spells = data[trait]
                        if len(innate_spells) == 0:
                            continue
                        if isinstance(innate_spells, list):
                            if len(innate_spells) >= 2:
                                last_value = innate_spells[-1]
                                if isinstance(last_value, int):
                                    del innate_spells[-1]
                                    data[trait] = sample(innate_spells, last_value)
                        elif isinstance(innate_spells, dict):
                            spell_list = list()
                            innate_spells = self._truncate_dict(data[trait], level)
                            for _, spells in innate_spells.items():
                                for spell in spells:
                                    spell_list.append(spell)
                            data[trait] = spell_list
                elif trait == "languages":
                    data[trait] += subrace_data[trait]
                elif trait == "proficiency":
                    subrace_proficiency_types = subrace_data[trait]
                    for category in tuple(subrace_proficiency_types.keys()):
                        subrace_proficiencies = subrace_proficiency_types.get(category)
                        data[trait][category] += subrace_proficiencies
                elif trait == "skills":
                    data[trait] += subrace_data[trait]
                elif trait == "ratio":
                    if data[trait] is None:
                        subrace_ratio = subrace_data[trait]
                        data[trait] = subrace_ratio
                elif trait == "resistances":
                    data[trait] += subrace_data[trait]
                elif trait == "traits":
                    for other in subrace_data.get(trait):
                        data[trait].append(other)

        # Calculate height/weight
        height_base = data.get("ratio").get("height").get("base")
        height_modifier = data.get("ratio").get("height").get("modifier")
        height_modifier = sum(list(roll(height_modifier)))
        weight_base = data.get("ratio").get("weight").get("base")
        weight_modifier = data.get("ratio").get("weight").get("modifier")
        weight_modifier = sum(list(roll(weight_modifier)))
        data["height"] = height_base + height_modifier
        data["weight"] = (height_modifier * weight_modifier) + weight_base
        del data["ratio"]

        return data


class Yari(_YariBuilder):
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
        super(Yari, self).__init__(
            race, subrace, klass, subclass, level, sex, background
        )
        rdata = self._build_race(self.race, self.subrace, self.level)
        cdata = self._build_class(self.klass, self.subclass, self.level, rdata)
        self.abilities = cdata.get("abilities")
        self.ancestor = None
        self.armors = rdata.get("proficiency").get("armors") + cdata.get(
            "proficiency"
        ).get("armors")
        self.bonus = rdata.get("bonus")
        self.bonusmagic = cdata.get("bonusmagic")
        self.darkvision = rdata.get("darkvision")
        self.equipment = cdata.get("equipment")
        self.features = cdata.get("features")
        self.height = rdata.get("height")
        self.hitdie = cdata.get("hit_die")
        self.hitpoints = cdata.get("hitpoints")
        self.innatemagic = rdata.get("innatemagic")
        self.languages = rdata.get("languages")
        self.proficiencybonus = get_proficiency_bonus(self.level)
        self.resistances = rdata.get("resistances")
        self.savingthrows = cdata.get("savingthrows")
        self.size = rdata.get("size")
        self.skills = cdata.get("skills")
        self.speed = rdata.get("speed")
        self.spellslots = cdata.get("spellslots")
        self.tools = rdata.get("proficiency").get("tools") + cdata.get(
            "proficiency"
        ).get("tools")
        self.traits = rdata.get("traits")
        self.weapons = rdata.get("proficiency").get("weapons") + cdata.get(
            "proficiency"
        ).get("weapons")
        self.weight = rdata.get("weight")

    def run(self):
        for rank, options in self.abilities.items():
            if isinstance(options, list):
                ability_options_list = "\n".join(options)
                ability_choice = prompt(
                    f"Choose your primary ability:\n\n{ability_options_list}\n\n>",
                    options,
                )
                self.abilities[rank] = ability_choice
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
