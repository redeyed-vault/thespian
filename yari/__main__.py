import argparse
from random import choice

from yari import (
    Yari,
    get_character_classes,
    get_character_races,
    get_subclasses_by_class,
    get_subraces_by_race,
    prompt,
)


def main():
    app = argparse.ArgumentParser(prog="Yari", description="Yari character maker.")
    app.add_argument(
        "-race",
        "-r",
        help="sets character's race",
        type=str,
        choices=get_character_races(),
        default="Human",
    )
    app.add_argument(
        "-subrace", "-sr", help="sets character's subrace", type=str, default=""
    )
    app.add_argument(
        "-klass",
        "-k",
        help="sets character's class",
        type=str,
        choices=get_character_classes(),
        default="Fighter",
    )
    app.add_argument(
        "-subclass", "-sc", help="sets character's subclass", type=str, default=""
    )
    app.add_argument(
        "-level",
        "-l",
        help="sets character's level",
        type=int,
        choices=tuple(range(1, 21)),
        default=1,
    )
    app.add_argument(
        "-sex",
        "-s",
        help="sets character's sex",
        type=str,
        choices=("Female", "Male"),
        default="Female",
    )
    app.add_argument(
        "-alignment",
        "-a",
        help="sets character's alignment",
        type=str,
        choices=(
            "Chaotic Evil",
            "Chaotic Good",
            "Chaotic Neutral",
            "Lawful Evil",
            "Lawful Good",
            "Lawful Neutral",
            "Neutral Evil",
            "Neutral Good",
            "True Neutral",
        ),
        default="True Neutral",
    )
    app.add_argument(
        "-background", "-b", help="sets character's background", type=str, default=""
    )
    args = app.parse_args()
    race = args.race
    subrace = args.subrace
    klass = args.klass
    subclass = args.subclass
    level = args.level
    sex = args.sex
    alignment = args.alignment
    background = args.background

    subraces = get_subraces_by_race(race)
    if len(subraces) > 0:
        if subrace == "":
            subrace = prompt("Choose your subrace", subraces)
        elif subrace not in subraces:
            subrace = prompt("Choose a valid subrace", subraces)

    subclasses = get_subclasses_by_class(klass)
    if subclass == "":
        subclass = prompt("Choose your subclass", subclasses)
    elif subclass not in subclasses:
        subclass = prompt("Choose a valid subclass", subclasses)

    f = Yari(race, subrace, klass, subclass, level, sex, background)
    f.run()

    print(f.abilities)
    print(f.ancestor)
    print(f.armors)
    print(f.bonus)
    print(f.bonusmagic)
    print(f.darkvision)
    print(f.equipment)
    print(f.features)
    print(f.height)
    print(f.hitdie)
    print(f.hitpoints)
    print(f.innatemagic)
    print(f.languages)
    print(f.proficiencybonus)
    print(f.resistances)
    print(f.savingthrows)
    print(f.scores)
    print(f.size)
    print(f.skills)
    print(f.speed)
    print(f.spellslots)
    print(f.tools)
    print(f.traits)
    print(f.weapons)
    print(f.weight)


if __name__ == "__main__":
    main()
