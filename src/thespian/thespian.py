from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentTypeError
from collections import namedtuple
import logging
from math import ceil

from attributes import AttributeGenerator, generate_hit_points, get_ability_modifier
from config.getters import (
    get_default_background,
    get_entry_background,
    get_entry_class,
    get_entry_race,
    get_entry_subclass,
    get_entry_subrace,
    get_pc_backgrounds,
    get_pc_classes,
    get_pc_races,
    get_pc_subclasses,
    get_pc_subraces,
    get_skill_ability,
    get_skill_list,
)
from httpd import Server
from metrics import AnthropometricCalculator
from notifications import initialize, prompt
from tweaks import AbilityScoreImprovement

__author__ = "Marcus T Taylor"
__version__ = "220706"


log = logging.getLogger("thespian")
log.setLevel(logging.INFO)
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.INFO)
log_format = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
log_handler.setFormatter(log_format)
log.addHandler(log_handler)


class UserPromptRecorder:
    """Class to store/recall user prompt selections."""

    prompt_inputs: dict = dict()

    def recall(self, prompt_category: str) -> dict:
        """Returns/creates (if non-existent) prompt saved to a specified category."""
        try:
            return self.prompt_inputs[prompt_category]
        except KeyError:
            self.prompt_inputs[prompt_category] = set()
            return self.prompt_inputs[prompt_category]

    def store(self, prompt_category: str, prompt_inputs: list) -> None:
        """Stores prompts to a specified category."""
        if prompt_category not in self.prompt_inputs:
            self.prompt_inputs[prompt_category] = set(prompt_inputs)
        else:
            self.prompt_inputs[prompt_category].update(prompt_inputs)


def define_background(background: str) -> dict:
    """Defines character background parameters."""
    try:
        background_base = get_entry_background(background)
    except KeyError:
        raise ValueError(f"Unknown background '{background}'.")

    blueprint = dict()
    guidelines = define_guidelines(background_base["guides"])
    return honor_guidelines(guidelines, background_base, blueprint, False)


def define_class(
    klass: str, level: int, racial_bonuses: dict, threshold: int, roll_hp: bool = False
) -> dict:
    """Defines character class parameters."""
    try:
        class_base = get_entry_class(klass)
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

    ability_options = list(class_base["primary_ability"].values())
    if not all(isinstance(a, str) for a in ability_options):
        for index, option in enumerate(ability_options):
            if isinstance(option, list):
                ranking = ("primary", "secondary")
                my_ability = prompt(
                    f"{ranking[index].capitalize()}: Choose a {ranking[index]} class attribute.", option
                )
                ability_options[index] = my_ability
                log.info(f"primary ability: You selected '{my_ability}'.")

    ability_options = tuple(ability_options)
    log.info("primary ability: You selected '" + ", ".join(ability_options) + "'.")

    try:
        blueprint["spell_slots"] = class_base["spell_slots"][level]
    except KeyError:
        blueprint["spell_slots"] = "0"

    guidelines = define_guidelines(class_base["guides"])
    blueprint = honor_guidelines(guidelines, class_base, blueprint)

    attributes = AttributeGenerator(
        ability_options, racial_bonuses, threshold
    ).generate()
    blueprint["scores"] = attributes

    hit_die, hit_points = generate_hit_points(
        level, class_base["hit_die"], attributes, roll_hp
    )
    blueprint["hit_die"] = hit_die
    blueprint["hit_points"] = hit_points
    return blueprint


def define_guidelines(guideline_string: str) -> dict | None:
    """Defines special racial and class generation guidelines."""
    if guideline_string is None:
        return None

    creation_guidelines = dict()
    for guide_pair_string in guideline_string.split("|"):
        guideline_value_pair = guide_pair_string.split(",")
        if len(guideline_value_pair) != 2:
            raise ValueError("Malformed guideline. Guidelines must have 2 values.")
        guideline_name, guide_increment = guideline_value_pair
        creation_guidelines[guideline_name] = int(guide_increment)

    # Check guideline increment value integrity.
    for guideline_increment_value in tuple(creation_guidelines.values()):
        if guideline_increment_value < 0:
            raise ValueError("Guideline increment values must be greater than 0.")
    return creation_guidelines


def define_race(race: str, sex: str, background: str, level: int) -> dict:
    """Define character race parameters."""
    try:
        race_base = get_entry_race(race)
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
    return honor_guidelines(guidelines, race_base, blueprint)


def define_subclass(subclass: str, level: int) -> dict:
    """Defines character subclass parameters."""
    try:
        subclass_base = get_entry_subclass(subclass)
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
    return honor_guidelines(guidelines, subclass_base, blueprint)


def define_subrace(subrace: str, level: int) -> dict:
    """Define character subrace parameters."""
    try:
        subrace_base = get_entry_subrace(subrace)
    except KeyError:
        raise ValueError(f"Unknown player subrace '{subrace}'.")

    blueprint = dict()
    blueprint["subrace"] = subrace
    blueprint["level"] = level
    blueprint["armors"] = subrace_base["armors"]
    blueprint["tools"] = subrace_base["tools"]
    blueprint["weapons"] = subrace_base["weapons"]
    blueprint["traits"] = subrace_base["traits"]

    guidelines = define_guidelines(subrace_base["guides"])
    return honor_guidelines(guidelines, subrace_base, blueprint)


def expand_ability(ability: str, scores: dict, skills: list) -> dict:
    """Expands an abilities' associated properties & skills."""
    ability_properties = dict()

    # Strength has three other unique properties.
    if ability == "Strength":
        ability_properties["carry_capacity"] = scores[ability] * 15
        ability_properties["push_pull_carry"] = ability_properties["carry_capacity"] * 2
        ability_properties["maximum_lift"] = ability_properties["push_pull_carry"]

    expanded_properties = {
        "score": scores[ability],
        "modifier": get_ability_modifier(ability, scores),
        "skills": skills,
    }
    if len(ability_properties) > 0:
        expanded_properties["properties"] = ability_properties
    return expanded_properties


def expand_skills(skills: list, scores: dict, proficiency_bonus: int = 2) -> dict:
    """Expands skill list with each skill's associated properties."""
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


def fuse_iterables(original_iterable: dict, fused_iterable: dict) -> dict:
    """Fuses a dictionary to the the original dictionary."""
    if not isinstance(original_iterable, dict) or not isinstance(fused_iterable, dict):
        raise TypeError("Both arguments must be of type 'dict'.")

    for key, value in fused_iterable.items():
        # If index not availble in root dictionary, create it.
        if key not in original_iterable:
            original_iterable[key] = value
            continue

        # Fuse dict values
        if isinstance(value, dict):
            dict_value = original_iterable[key]
            for subkey, subvalue in value.items():
                if dict_value is None:
                    break
                if subkey not in dict_value:
                    try:
                        original_iterable[key][subkey] = subvalue
                    except IndexError:
                        original_iterable[key] = subvalue
                else:
                    original_iterable[key][subkey] = dict_value.get(subkey) + subvalue
            continue

        # Fuse integer values
        if isinstance(value, int):
            int_value = original_iterable[key]
            if not isinstance(int_value, int):
                continue
            if value > int_value:
                original_iterable[key] = value

        # Fuse list values
        if isinstance(value, list):
            list_value = original_iterable[key]
            if isinstance(list_value, list):
                original_iterable[key] = list(set(list_value + value))
    return original_iterable


def honor_guidelines(
    guidelines: dict | None,
    blueprint: dict,
    output: dict,
    set_unuset_guidelines: bool = True,
) -> dict:
    """Parses and applies character guidelines."""
    if guidelines is None or not isinstance(guidelines, dict):
        return output

    recorder = UserPromptRecorder()

    for guideline, _ in guidelines.items():
        # TODO: Review this later - might be unnecessary
        # if guideline not in guidelines:
        #    continue

        # Copy guideline to blueprint, if not specified in blueprint (if allowed).
        if set_unuset_guidelines and guideline not in output:
            output[guideline] = None

        user_inputs = list()
        guide_increment = guidelines[guideline]

        # Special guideline "ancestry": Associated with Dragonborn characters.
        # Special guideline "bonus": Associated with racial ability bonuses.
        # Special guideline "primary_ability": Associated with class abilities.
        if guideline == "ancestry":
            if guide_increment != 1:
                continue

            ancestry_options = list(blueprint[guideline])
            my_selection = prompt("Choose your racial ancestry.", ancestry_options)
            user_inputs.append(my_selection)
            ancestry = user_inputs[0]
            output[guideline] = ancestry
            output["resistances"] = output["resistances"][ancestry]
            log.info(f"You chose '{ancestry}' as your dragon ancestry.")
            continue
        elif guideline == "bonus":
            bonus_options = dict(blueprint[guideline])
            bonus_choices = {k: v for k, v in bonus_options.items() if v < 2}.keys()
            user_inputs = {k: v for k, v in bonus_options.items() if v > 1}
            for _ in range(guide_increment):
                my_selection = prompt("Choose your racial bonus.", bonus_choices)
                user_inputs[my_selection] = 1
                log.info(f"You chose '{my_selection}' as your racial bonus.")

            output[guideline] = user_inputs
            continue

        # Guidelines with a 0 increment add ALL values by default.
        if guide_increment == 0:
            # Guideline "spells" work differently depending on option type (dict|list).
            # Other guidelines (not "spells") add all their values.
            if guideline == "spells":
                spell_list = blueprint[guideline]
                if len(spell_list) == 0:
                    continue
                # If dict, add all spells up to character's appropriate level.
                # If list, add all spells (as list) to character's spell list.
                if isinstance(spell_list, dict):
                    level = output["level"]
                    spell_list = {k: v for k, v in spell_list.items() if k <= level}
                    for l, spells in spell_list.items():
                        if l <= level:
                            user_inputs += spells
                    output[guideline] = user_inputs
                    recorder.store(guideline, user_inputs)
                elif isinstance(spell_list, list):
                    user_inputs += spell_list
                    output[guideline] = user_inputs
                    recorder.store(guideline, user_inputs)
            else:
                user_inputs = blueprint[guideline]
                output[guideline] = user_inputs
                recorder.store(guideline, user_inputs)
            continue

        guideline_options = list(blueprint[guideline])

        # Remove list type values from guideline_options.
        # Add list type values to user_inputs (Automatically added to character's selection pool).
        for index, option in enumerate(guideline_options):
            if isinstance(option, list):
                user_inputs = user_inputs + option
                del guideline_options[index]

        # Player can now make additional guideline selections == guide_increment.
        for _ in range(guide_increment):
            my_selection = prompt(
                f"Make a selection from the '{guideline}' options.",
                guideline_options,
                recorder.recall(guideline),
            )
            user_inputs.append(my_selection)
            log.info(f"{guideline}: You selected '{my_selection}'.")
            output[guideline] = user_inputs
            recorder.store(guideline, user_inputs)

    return output


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
        fuse_iterables(my_race, my_subrace)
    my_background = define_background(background)
    fuse_iterables(my_race, my_background)
    height, weight = AnthropometricCalculator(race, sex, subrace).calculate()
    my_race["height"] = height
    my_race["weight"] = weight
    feet, inches = my_race["height"]
    log.info(f"Your height is {feet}' {inches}\".")
    log.info(f"your weight is {my_race['weight']}.")
    fuse_iterables(blueprint, my_race)

    my_class = define_class(klass, level, blueprint["bonus"], threshold, roll_hp)
    my_class["subclass"] = subclass
    if subclass == "":
        log.warn("No subclass options are available prior to level 3.")
    else:
        my_subclass = define_subclass(subclass, level)
        fuse_iterables(my_class, my_subclass)
    fuse_iterables(blueprint, my_class)
    order_dict(blueprint)
    AbilityScoreImprovement(blueprint).run()

    character = namedtuple("MyCharacter", blueprint.keys())(*blueprint.values())
    feet, inches = character.height
    proficiency_bonus = ceil(1 + (character.level / 4))

    features = list()
    for _, feature_list in character.features.items():
        features += feature_list

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
        "strength": expand_ability("Strength", character.scores, character.skills),
        "dexterity": expand_ability("Dexterity", character.scores, character.skills),
        "constitution": expand_ability(
            "Constitution", character.scores, character.skills
        ),
        "intelligence": expand_ability(
            "Intelligence", character.scores, character.skills
        ),
        "wisdom": expand_ability("Wisdom", character.scores, character.skills),
        "charisma": expand_ability("Charisma", character.scores, character.skills),
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
        default="",
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

    background = args.background
    if background == "" or background not in get_pc_backgrounds():
        background = get_default_background(klass)

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
        background,
        klass,
        subclass,
        level,
        args.threshold,
        port,
        args.roll_hp,
    )
    Server.run(character, port)
