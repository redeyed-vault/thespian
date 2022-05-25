from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentTypeError
from collections import namedtuple
import logging
from math import ceil

from attributes import AttributeGenerator, generate_hit_points, get_ability_modifier
from tweaks import AbilityScoreImprovement
from httpd import Server
from sourcetree import SourceTree
from sourcetree.metrics import AnthropometricCalculator
from sourcetree.utils import (
    get_pc_backgrounds,
    get_pc_classes,
    get_pc_races,
    get_pc_subclasses,
    get_pc_subraces,
    get_skill_ability,
    get_skill_list,
)
from stdio import InputRecorder, initialize, prompt

__version__ = "220525"


log = logging.getLogger("thespian")
log.setLevel(logging.INFO)
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.INFO)
log_format = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
log_handler.setFormatter(log_format)
log.addHandler(log_handler)

recorder = InputRecorder()


class AttributeWriter:
    """Formats and prints attribute properties."""

    def __init__(self, attribute: str, scores: dict, skills: list):
        self.attribute = attribute
        self.scores = scores
        self.skills = skills
        self.properties = dict()

        # Strength has three other unique properties.
        if attribute == "Strength":
            strength_score = self.scores[attribute]
            self.properties["carry_capacity"] = strength_score * 15
            self.properties["push_pull_carry"] = self.properties["carry_capacity"] * 2
            self.properties["maximum_lift"] = self.properties["push_pull_carry"]

    @classmethod
    def out(cls, attribute, scores, skills) -> dict:
        o = cls(attribute, scores, skills)
        properties = {
            "score": o.scores[o.attribute],
            "modifier": get_ability_modifier(o.attribute, o.scores),
            "skills": o.skills,
        }
        if len(o.properties) > 0:
            properties["properties"] = o.properties
        return properties


# Testing - not fully implemented
def honor_guidelines(
    guidelines: dict | None,
    blueprint: dict,
    blueprint_base: dict,
    set_unused_guide: bool = True,
) -> dict:
    if guidelines is None:
        return blueprint

    for guideline, _ in guidelines.items():
        # TODO: Review this later - might be unnecessary
        # if guideline not in guidelines:
        #    continue

        # Copy guideline to blueprint, if not specified in blueprint (if allowed).
        if set_unused_guide and guideline not in blueprint:
            blueprint[guideline] = None

        user_inputs = list()
        guide_increment = guidelines[guideline]

        # Special guideline "ancestry": Associated with Dragonborn characters.
        # Special guideline "bonus": Associated with racial ability bonuses.
        # Special guideline "primary_ability": Associated with class abilities.
        if guideline == "ancestry":
            if guide_increment != 1:
                continue
            ancestry_options = list(blueprint_base[guideline])
            stdio = prompt("Choose your racial ancestry.", ancestry_options)
            user_inputs.append(stdio)
            ancestry = user_inputs[0]
            blueprint[guideline] = ancestry
            blueprint["resistances"] = blueprint["resistances"][ancestry]
            log.info(f"You chose '{ancestry}' as your dragon ancestry.")
            continue
        elif guideline == "bonus":
            bonus_options = dict(blueprint_base[guideline])
            bonus_choices = {k: v for k, v in bonus_options.items() if v < 2}.keys()
            user_inputs = {k: v for k, v in bonus_options.items() if v > 1}
            for _ in range(guide_increment):
                stdio = prompt("Choose your racial bonus.", bonus_choices)
                user_inputs[stdio] = 1
                log.info(f"You chose '{stdio}' as your racial bonus.")

            blueprint[guideline] = user_inputs
            continue
        elif guideline == "primary_ability":
            ability_options = list(blueprint_base[guideline].values())
            for index, option in enumerate(ability_options):
                if isinstance(option, list):
                    my_ability = prompt(
                        "Choose your class' primary ability/abilities.", option
                    )
                    ability_options[index] = my_ability
            user_inputs = tuple(ability_options)
            blueprint[guideline] = user_inputs
            recorder.store(guideline, user_inputs)
            log.info(guideline + ": You selected '" + ", ".join(user_inputs) + "'.")
            continue

        # Guidelines with a 0 increment add ALL values.
        if guide_increment == 0:
            # Guideline "spells" work differently depending on type.
            # Other guidelines (not "spells") add all their values.
            if guideline == "spells":
                spell_list = blueprint_base[guideline]
                if len(spell_list) == 0:
                    continue
                # If dict, add all spells up to character's appropriate level.
                # If list, add all spells (as list) to character's spell list.
                if isinstance(spell_list, dict):
                    spell_list = {k: v for k, v in spell_list.items() if k <= level}
                    for l, spells in spell_list.items():
                        if l <= level:
                            user_inputs += spells
                    blueprint[guideline] = user_inputs
                    recorder.store(guideline, user_inputs)
                elif isinstance(spell_list, list):
                    user_inputs += spell_list
                    blueprint[guideline] = user_inputs
                    recorder.store(guideline, user_inputs)
            else:
                user_inputs = blueprint_base[guideline]
                blueprint[guideline] = user_inputs
                recorder.store(guideline, user_inputs)
            continue

        # Remove list type guideline options.
        other_options = list(blueprint_base[guideline])
        for index, option in enumerate(other_options):
            if isinstance(option, list):
                user_inputs = user_inputs + option
                del other_options[index]

        for _ in range(guide_increment):
            #TODO: Fix prompt text for situation usage.
            stdio = prompt(
                f"Choose your character's racial {guideline}.",
                other_options,
                recorder.recall(guideline),
            )
            user_inputs.append(stdio)
            log.info(f"{guideline}: You selected '{stdio}'.")
            blueprint[guideline] = user_inputs
            recorder.store(guideline, user_inputs)
    return blueprint


def define_background(background: str) -> dict:
    """Defines character background parameters."""
    try:
        background_base = SourceTree.backgrounds[background]
    except KeyError:
        raise ValueError(f"Unknown background '{background}'.")

    blueprint = dict()
    guidelines = define_guidelines(background_base["guides"])
    return honor_guidelines(guidelines, blueprint, background_base, False)


def define_class(
    klass: str, level: int, racial_bonuses: dict, threshold: int, roll_hp: bool = False
) -> dict:
    """Defines character class parameters."""
    try:
        class_base = SourceTree.classes[klass]
    except KeyError:
        raise ValueError(f"Unknown player class '{klass}'.")

    blueprint = dict()
    blueprint["armors"] = class_base["armors"]
    blueprint["tools"] = class_base["tools"]
    blueprint["weapons"] = class_base["weapons"]
    blueprint["bonus_magic"] = dict()
    blueprint["feats"] = list()
    blueprint["features"] = {
        k: v for k, v in class_base["features"].items() if k <= level
    }
    blueprint["klass"] = klass
    blueprint["proficiency_bonus"] = ceil((level / 4) + 1)
    blueprint["saves"] = class_base["saves"]

    if roll_hp:
        log.warn("Hit points will be randomly generated every level after the first.")
    else:
        log.warn("Hit points will be assigned a fixed number every level.")

    try:
        blueprint["spell_slots"] = {
            k: v for k, v in class_base["spell_slots"].items() if k == level
        }
        blueprint["spell_slots"] = class_base["spell_slots"][level]
    except KeyError:
        blueprint["spell_slots"] = "0"

    guidelines = define_guidelines(class_base["guides"])
    blueprint = honor_guidelines(guidelines, blueprint, class_base)
    attributes = AttributeGenerator(
        blueprint["primary_ability"], racial_bonuses, threshold
    ).generate()
    blueprint["scores"] = attributes
    hit_die, hit_points = generate_hit_points(
        level, class_base["hit_die"], attributes, roll_hp
    )
    blueprint["hit_die"] = hit_die
    blueprint["hit_points"] = hit_points
    return blueprint


def define_guidelines(guides: str) -> dict | None:
    """Defines special racial and class guidelines."""
    if guides is None:
        return None
    creation_guides = dict()
    for guide in guides.split("|"):
        (guide_name, guide_increment) = guide.split(",")
        creation_guides[guide_name] = int(guide_increment)

    # Check guideline integrity.
    for value in tuple(creation_guides.values()):
        if value < 0:
            raise ValueError("Guide increment values must be greater than 0.")

    return creation_guides


def define_race(race: str, sex: str, background: str, level: int) -> dict:
    """Define character race parameters."""
    try:
        race_base = SourceTree.races[race]
    except KeyError:
        raise ValueError(f"Unknown player race '{race}'.")

    blueprint = dict()
    blueprint["ancestry"] = ""
    blueprint["background"] = background
    blueprint["level"] = level
    blueprint["race"] = race
    blueprint["sex"] = sex
    blueprint["armors"] = race_base["armors"]
    blueprint["bonus"] = race_base["bonus"]
    blueprint["languages"] = race_base["languages"]
    blueprint["resistances"] = race_base["resistances"]
    blueprint["size"] = race_base["size"]
    blueprint["speed"] = race_base["speed"]
    blueprint["spells"] = race_base["spells"]
    blueprint["tools"] = race_base["tools"]
    blueprint["traits"] = race_base["traits"]
    blueprint["weapons"] = race_base["weapons"]

    alignment_options = (
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
    alignment = prompt("Choose your alignment:", alignment_options)
    blueprint["alignment"] = alignment
    log.info(f"Your alignment is '{alignment}'.")

    guidelines = define_guidelines(race_base["guides"])
    blueprint = honor_guidelines(guidelines, blueprint, race_base)
    return blueprint


def define_subclass(subclass: str, level: int) -> dict:
    """Defines character subclass parameters."""
    try:
        subclass_base = SourceTree.subclasses[subclass]
    except KeyError:
        raise ValueError(f"Unknown player subclass '{subclass}'.")

    blueprint = dict()
    blueprint["armors"] = subclass_base["armors"]
    blueprint["tools"] = subclass_base["tools"]
    blueprint["weapons"] = subclass_base["weapons"]
    blueprint["bonus_magic"] = {
        l: ", ".join(s) for l, s in subclass_base["bonus_magic"].items() if l <= level
    }
    blueprint["feats"] = list()
    blueprint["features"] = {
        k: v for k, v in subclass_base["features"].items() if k <= level
    }
    blueprint["subclass"] = subclass

    guidelines = define_guidelines(subclass_base["guides"])
    blueprint = honor_guidelines(guidelines, blueprint, subclass_base)
    return blueprint


def define_subrace(subrace: str, level: int) -> dict:
    """Define character subrace parameters."""
    try:
        subrace_base = SourceTree.subraces[subrace]
    except KeyError:
        raise ValueError(f"Unknown player subrace '{subrace}'.")

    blueprint = dict()
    blueprint["subrace"] = subrace
    blueprint["armors"] = subrace_base["armors"]
    blueprint["tools"] = subrace_base["tools"]
    blueprint["weapons"] = subrace_base["weapons"]
    blueprint["traits"] = subrace_base["traits"]

    guidelines = define_guidelines(subrace_base["guides"])
    blueprint = honor_guidelines(guidelines, blueprint, subrace_base)
    return blueprint


def expand_skills(skills: list, scores: dict, proficiency_bonus: int = 2) -> dict:
    """Returns an expanded skill list."""
    expanded_skills = dict()
    for skill in get_skill_list():
        ability = get_skill_ability(skill)
        modifier = get_ability_modifier(ability, scores)

        if skill in skills:
            rank = proficiency_bonus + modifier
            class_skill = True
        else:
            rank = modifier
            class_skill = False

        expanded_skills[skill] = {
            "ability": ability,
            "rank": rank,
            "is_class_skill": class_skill,
        }
    return expanded_skills


def merge_dicts(dict_1: dict, dict_2: dict) -> dict:
    """Merges dictionaries."""
    if not isinstance(dict_1, dict):
        raise TypeError("First parameter must be of type 'dict'.")

    if not isinstance(dict_2, dict):
        raise TypeError("Second parameter must be of type 'dict'.")

    for key, value in dict_2.items():
        # If index not availble in root dictionary.
        if key not in dict_1:
            dict_1[key] = value
            continue

        # Merge dicts
        if isinstance(value, dict):
            a_dict = dict_1[key]
            for subkey, subvalue in value.items():
                if a_dict is None:
                    break
                if subkey not in a_dict:
                    try:
                        dict_1[key][subkey] = subvalue
                    except IndexError:
                        dict_1[key] = subvalue
                else:
                    dict_1[key][subkey] = a_dict.get(subkey) + subvalue
            continue

        # Merge integers
        if isinstance(value, int):
            a_int = dict_1[key]
            if not isinstance(a_int, int):
                continue
            if value > a_int:
                dict_1[key] = value

        # Merge lists
        if isinstance(value, list):
            a_list = dict_1[key]
            if isinstance(a_list, list):
                dict_1[key] = list(set(a_list + value))

    return dict_1


def order_dict(iter: dict) -> dict:
    """Reorders dict by dictionary keys."""
    reordered_iter = dict()
    iter_keys = sorted(iter)
    if len(iter_keys) == 0:
        return iter
    for key in iter_keys:
        reordered_iter[key] = iter[key]
    return reordered_iter


def thespian(
    race: str,
    subrace: str,
    sex: str,
    background: str,
    klass: str,
    subclass: str,
    level: int,
    threshold: int,
    port: int,
    roll_hp: bool,
) -> dict:
    """Runs the thespian character generator."""
    initialize(race, subrace, sex, background, klass, subclass, level, threshold, port)

    blueprint = dict()
    blueprint["subrace"] = subrace
    my_race = define_race(race, sex, background, level)
    if subrace == "":
        log.warn(f"No subrace options are available for '{race}'.")
    else:
        my_subrace = define_subrace(subrace, level)
        merge_dicts(my_race, my_subrace)
    my_background = define_background(background)
    merge_dicts(my_race, my_background)
    height, weight = AnthropometricCalculator(race, sex, subrace).calculate()
    my_race["height"] = height
    my_race["weight"] = weight
    feet, inches = my_race["height"]
    log.info(f"Your height is {feet}' {inches}\".")
    log.info(f"your weight is {my_race['weight']}.")
    merge_dicts(blueprint, my_race)
    my_class = define_class(klass, level, blueprint["bonus"], threshold, roll_hp)
    my_class["subclass"] = subclass
    if subclass == "":
        log.warn("No subclass options are available prior to level 3.")
    else:
        my_subclass = define_subclass(subclass, level)
        merge_dicts(my_class, my_subclass)
    merge_dicts(blueprint, my_class)
    order_dict(blueprint)
    AbilityScoreImprovement(blueprint).run()

    character = namedtuple("MyCharacter", blueprint.keys())(*blueprint.values())
    feet, inches = character.height
    proficiency_bonus = ceil(1 + (character.level / 4))
    features = list()
    for _, feature in character.features.items():
        features += feature
    return {
        "race": character.race,
        "ancestry": character.ancestry,
        "subrace": character.subrace,
        "sex": character.sex,
        "alignment": character.alignment,
        "background": character.background,
        "feet": feet,
        "inches": inches,
        "weight": character.weight,
        "size": character.size,
        "class": character.klass,
        "subclass": character.subclass,
        "level": character.level,
        "hit_points": character.hit_points,
        "proficiency_bonus": proficiency_bonus,
        "strength": AttributeWriter.out("Strength", character.scores, character.skills),
        "dexterity": AttributeWriter.out(
            "Dexterity", character.scores, character.skills
        ),
        "constitution": AttributeWriter.out(
            "Constitution", character.scores, character.skills
        ),
        "intelligence": AttributeWriter.out(
            "Intelligence", character.scores, character.skills
        ),
        "wisdom": AttributeWriter.out("Wisdom", character.scores, character.skills),
        "charisma": AttributeWriter.out("Charisma", character.scores, character.skills),
        "speed": character.speed,
        "initiative": get_ability_modifier("Dexterity", character.scores),
        "armors": character.armors,
        "tools": character.tools,
        "weapons": character.weapons,
        "languages": character.languages,
        "saves": character.saves,
        "skills": expand_skills(character.skills, character.scores, proficiency_bonus),
        "feats": character.feats,
        "traits": character.traits,
        "features": features,
        "spell_slots": character.spell_slots,
        "bonus_magic": character.bonus_magic,
        "spells": character.spells,
        "equipment": character.equipment,
    }


def main() -> None:
    app = ArgumentParser(
        description="Generate 5th edition Dungeons & Dragons characters.",
        formatter_class=ArgumentDefaultsHelpFormatter,
        prog=f"thespian (ver. {__version__})",
    )
    app.add_argument(
        "-race",
        "-r",
        help="Sets your character's race",
        type=str,
        choices=get_pc_races(),
        default="Human",
    )
    app.add_argument(
        "-subrace",
        "-sr",
        help="Sets your character's subrace",
        type=str,
        default="",
    )
    app.add_argument(
        "-sex",
        "-s",
        help="Sets your character's sex",
        type=str,
        choices=("Female", "Male"),
        default="Female",
    )
    app.add_argument(
        "-background",
        "-b",
        help="Sets your character's background",
        type=str,
        choices=get_pc_backgrounds(),
        default="Soldier",
    )
    app.add_argument(
        "-klass",
        "-k",
        help="Sets your character's class",
        type=str,
        choices=get_pc_classes(),
        default="Fighter",
    )
    app.add_argument(
        "-subclass",
        "-sc",
        help="Sets your character's subclass",
        type=str,
        default="",
    )
    app.add_argument(
        "-level",
        "-l",
        help="Sets your character's level",
        type=int,
        choices=list(range(1, 21)),
        default=1,
    )
    app.add_argument(
        "-threshold",
        "-t",
        help="Sets the minimum ability score threshold",
        type=int,
        default=65,
    )
    app.add_argument(
        "-port",
        "-p",
        help="Sets server's port",
        type=int,
        default=5000,
    )
    app.add_argument(
        "--roll-hp",
        action="store_true",
        default=False,
        dest="roll_hp",
        help="Roll hit points every level after the first",
    )

    args = app.parse_args()
    race = args.race
    subrace = args.subrace
    klass = args.klass
    subclass = args.subclass
    level = args.level
    port = args.port

    if level < 3:
        subclass = ""
    else:
        subclasses = get_pc_subclasses(klass)
        if subclass not in subclasses:
            raise ArgumentTypeError(
                f"Invalid subclass option '{subclass}'. Valid options for {klass} > {subclasses}"
            )

    subraces = get_pc_subraces(race)
    if len(subraces) != 0 and subrace not in subraces:
        raise ArgumentTypeError(
            f"Invalid subrace option '{subrace}'. Valid options for {race} > {subraces}"
        )

    character = thespian(
        race,
        subrace,
        args.sex,
        args.background,
        klass,
        subclass,
        level,
        args.threshold,
        port,
        args.roll_hp,
    )
    with Server(character, port) as http:
        http.run()
