from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentTypeError
from collections import namedtuple
import logging
from math import ceil
from random import randint

from attributes import AttributeGenerator
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
)
from stdio import InputRecorder, initialize, prompt

__version__ = "220506"


log = logging.getLogger("thespian")
log.setLevel(logging.INFO)
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.INFO)
log_format = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
log_handler.setFormatter(log_format)
log.addHandler(log_handler)

recorder = InputRecorder()


def define_background(background: str) -> dict:
    """Defines character background parameters."""
    try:
        background_base = SourceTree.backgrounds[background]
    except KeyError:
        raise ValueError(f"Unknown background '{background}'.")

    blueprint = dict()
    guidelines = define_guidelines(background_base["guides"])
    if guidelines is None:
        return blueprint

    for guideline, _ in guidelines.items():
        if guideline not in guidelines:
            continue
        if guideline not in blueprint:
            blueprint[guideline] = None

        user_inputs = list()
        guide_increment = guidelines[guideline]

        # 0 increment items are added entirely.
        if guide_increment == 0:
            user_inputs = background_base[guideline]
            blueprint[guideline] = user_inputs
            recorder.store(guideline, user_inputs)
            continue

        # Remove options of list type from the guidelines.
        other_options = list(background_base[guideline])
        for index, option in enumerate(other_options):
            if isinstance(option, list):
                user_inputs = user_inputs + option
                del other_options[index]

        for _ in range(guide_increment):
            stdio = prompt(
                f"Choose your background '{guideline}.",
                other_options,
                recorder.recall(guideline),
            )
            user_inputs.append(stdio)
            log.info(f"{guideline}: You selected '{stdio}'.")
            blueprint[guideline] = user_inputs
            recorder.store(guideline, user_inputs)

    return blueprint


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
    blueprint["bonusmagic"] = None
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

    hit_die = int(class_base["hit_die"])
    blueprint["hit_die"] = f"{level}d{hit_die}"
    blueprint["hit_points"] = hit_die
    if level > 1:
        die_rolls = list()
        for _ in range(0, level - 1):
            if not roll_hp:
                hp_result = int((hit_die / 2) + 1)
            else:
                hp_result = randint(1, hit_die)
            die_rolls.append(hp_result)
        blueprint["hit_points"] += sum(die_rolls)
    log.info(f"You have {blueprint['hit_points']} hit points.")

    try:
        blueprint["spell_slots"] = {
            k: v for k, v in class_base["spell_slots"].items() if k == level
        }
        blueprint["spell_slots"] = class_base["spell_slots"][level]
    except KeyError:
        blueprint["spell_slots"] = "0"

    guidelines = define_guidelines(class_base["guides"])
    if guidelines is not None:
        for guideline, _ in guidelines.items():
            if guideline not in guidelines:
                continue
            if guideline not in blueprint:
                blueprint[guideline] = None

            user_inputs = list()
            guide_increment = guidelines[guideline]

            if guideline == "primary_ability":
                ability_options = list(class_base[guideline].values())
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

            # 0 increment items are added entirely.
            if guide_increment == 0:
                user_inputs = list(class_base[guideline])
                blueprint[guideline] = user_inputs
                recorder.store(guideline, user_inputs)
                continue

            # Remove options of list type from the guidelines.
            other_options = list(class_base[guideline])
            for index, option in enumerate(other_options):
                if isinstance(option, list):
                    user_inputs = user_inputs + option
                    del other_options[index]

            for _ in range(guide_increment):
                my_ability = prompt(
                    f"Choose your class' {guideline}.",
                    other_options,
                    recorder.recall(guideline),
                )
                user_inputs.append(my_ability)
                blueprint[guideline] = user_inputs
                recorder.store(guideline, user_inputs)
                log.info(f"{guideline}: You selected '{my_ability}'.")

    blueprint["scores"] = AttributeGenerator(
        blueprint["primary_ability"], racial_bonuses, threshold
    ).generate()

    return blueprint


def define_guidelines(guides) -> dict | None:
    """Defines special racial and class guidelines."""
    if guides is not None:
        creation_guides = dict()
        for guide in guides.split("|"):
            (guide_name, guide_increment) = guide.split(",")
            creation_guides[guide_name] = int(guide_increment)

        # Check guideline integrity.
        for value in tuple(creation_guides.values()):
            if value < 0:
                raise ValueError("Guide increment values must be greater than 0.")

        return creation_guides

    return None


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
    if guidelines is None:
        return blueprint

    for guideline, _ in guidelines.items():
        if guideline not in guidelines:
            continue
        if guideline not in blueprint:
            blueprint[guideline] = None

        user_inputs = list()
        guide_increment = guidelines[guideline]

        if guideline == "ancestry":
            if guide_increment != 1:
                continue

            ancestry_options = list(race_base[guideline])
            stdio = prompt("Choose your racial ancestry.", ancestry_options)
            user_inputs.append(stdio)
            ancestry = user_inputs[0]
            blueprint[guideline] = ancestry
            blueprint["resistances"] = blueprint["resistances"][ancestry]
            log.info(f"You chose '{ancestry}' as your dragon ancestry.")
            continue
        elif guideline == "bonus":
            bonus_options = dict(race_base[guideline])
            bonus_choices = {k: v for k, v in bonus_options.items() if v < 2}.keys()
            user_inputs = {k: v for k, v in bonus_options.items() if v > 1}
            for _ in range(guide_increment):
                stdio = prompt("Choose your racial bonus.", bonus_choices)
                user_inputs[stdio] = 1
                log.info(f"You chose '{stdio}' as your racial bonus.")

            blueprint[guideline] = user_inputs
            continue

        # 0 increment items are added entirely.
        if guide_increment == 0:
            if guideline == "spells":
                spell_list = race_base[guideline]
                # Ignore guideline if no spells defined.
                if len(spell_list) == 0:
                    continue

                # If dict, add all spells up to character's appropriate level.
                # If list, add all spells to character's spell list.
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
                user_inputs = race_base[guideline]
                blueprint[guideline] = user_inputs
                recorder.store(guideline, user_inputs)
            continue

        # Remove list type guideline options.
        other_options = list(race_base[guideline])
        for index, option in enumerate(other_options):
            if isinstance(option, list):
                user_inputs = user_inputs + option
                del other_options[index]

        for _ in range(guide_increment):
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
    blueprint["bonusmagic"] = dict()
    blueprint["feats"] = list()
    blueprint["features"] = {
        k: v for k, v in subclass_base["features"].items() if k <= level
    }
    blueprint["subclass"] = subclass

    guidelines = define_guidelines(subclass_base["guides"])
    if guidelines is None:
        return blueprint

    for guideline, _ in guidelines.items():
        if guideline not in guidelines:
            continue
        if guideline not in blueprint:
            blueprint[guideline] = None

        user_inputs = list()
        guide_increment = guidelines[guideline]

        # 0 increment items are added entirely.
        if guide_increment == 0:
            user_inputs = list(subclass_base[guideline])
            blueprint[guideline] = user_inputs
            recorder.store(guideline, user_inputs)
            continue

        # Remove options of list type from the guidelines.
        other_options = list(subclass_base[guideline])
        for index, option in enumerate(other_options):
            if isinstance(option, list):
                user_inputs = user_inputs + option
                del other_options[index]

        for _ in range(guide_increment):
            stdio = prompt(
                f"Choose your class' {guideline}.",
                other_options,
                recorder.recall(guideline),
            )
            user_inputs.append(stdio)
            log.info(f"{guideline}: You selected '{stdio}'.")
            blueprint[guideline] = user_inputs
            recorder.store(guideline, user_inputs)

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
    if guidelines is not None:
        for guideline, _ in guidelines.items():
            if guideline not in guidelines:
                continue

            user_inputs = list()
            guide_increment = guidelines[guideline]

            # 0 increment items are added entirely.
            if guide_increment == 0:
                if guideline == "spells":
                    spell_list = subrace_base[guideline]
                    # Ignore if no spells defined.
                    if len(spell_list) == 0:
                        continue

                    # If dict, add all spells up to character's appropriate level.
                    # If list, add all spells to character's spell list.
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
                    user_inputs = subrace_base[guideline]
                    blueprint[guideline] = user_inputs
                    recorder.store(guideline, user_inputs)
                continue

            # Remove list type guideline options.
            other_options = list(guidelines[guideline])
            for index, option in enumerate(other_options):
                if isinstance(option, list):
                    user_inputs = user_inputs + option
                    del other_options[index]

            for _ in range(guide_increment):
                stdio = prompt(
                    f"Choose your character's sub-racial {guideline}.",
                    other_options,
                    recorder.recall(guideline),
                )
                user_inputs.append(stdio)
                log.info(f"{guideline}: You selected '{stdio}'.")
                blueprint[guideline] = user_inputs
                recorder.store(guideline, user_inputs)

    return blueprint


def merge_dicts(dict_1: dict, dict_2: dict) -> dict:
    """Merges two dictionaries."""
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
) -> namedtuple:
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
    return namedtuple("MyChar", blueprint.keys())(*blueprint.values())


def main():
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
