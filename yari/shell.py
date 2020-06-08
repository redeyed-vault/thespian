from collections import OrderedDict

import click

from yari.classes import *
from yari.attributes import AttributeGenerator
from yari.improvement import ImprovementGenerator
from yari.proficiency import ProficiencyGenerator
from yari.races import *
from yari.skills import SkillGenerator
from yari.version import __version__
from yari.reader import reader
from yari.writer import Writer


@click.command()
@click.option("-file", default="", help="Character sheet file name.", type=str)
@click.option("-race", default="", help="Character's chosen race.", type=str)
@click.option("-subrace", default="", help="Character's chosen subrace.", type=str)
@click.option("-sex", default="", help="Character's chosen gender.", type=str)
@click.option(
    "-background", default="", help="Character's chosen background.", type=str
)
@click.option(
    "-klass", default="", help="Character's chosen class.", type=str,
)
@click.option(
    "-path",
    default="",
    help="Character's chosen path (archetype, domain, path, etc)",
    type=str,
)
@click.option("-level", default=1, help="Character's class level.", type=int)
@click.option(
    "-variant", default="false", help="Use variant rules (Humans only).", type=str,
)
@click.version_option(prog_name="Yari", version=__version__)
def main(
    file: str,
    race: str,
    subrace: str,
    sex: str,
    background: str,
    klass: str,
    path: str,
    level: int,
    variant: bool,
) -> None:
    def out(message: str, is_error=False, is_warning=False):
        if is_error:
            click.secho(f"error: {message}", bold=True, fg="red")
            exit()
        elif is_warning:
            click.secho(f"warning: {message}", bold=True, fg="yellow")
        else:
            click.secho(f"success: {message}", bold=True, fg="bright_green")

    # Handle application argument processing.
    if race != "":
        if race not in reader("races"):
            out(f"invalid character race '{race}'", is_error=True)
    else:
        race = random.choice(reader("races"))

    valid_subraces = [r for r in get_subraces_by_race(race)]
    if subrace == "":
        if len(valid_subraces) is not 0:
            subrace = random.choice(valid_subraces)
    else:
        try:
            if len(valid_subraces) is 0:
                raise ValueError(f"race '{race}' has no available subraces")

            if subrace not in valid_subraces:
                raise ValueError(f"invalid subrace race '{subrace}'")
        except ValueError as e:
            out(str(e), is_error=True)

    the_sexes = ["Female", "Male"]
    if sex in the_sexes:
        sex = sex
    else:
        sex = random.choice(the_sexes)

    if klass == "":
        klass = random.choice(reader("classes"))
    else:
        try:
            if klass not in reader("classes"):
                raise ValueError
        except ValueError:
            out(f"invalid character class '{klass}'", is_error=True)

    if background == "":
        background = reader("classes", (klass,)).get("background")
    else:
        valid_backgrounds = reader("backgrounds")
        if background not in valid_backgrounds:
            out(f"invalid character background '{background}'", is_error=True)

    valid_class_paths = get_paths_by_class(klass)
    if path == "":
        path = random.choice(valid_class_paths)
    else:
        if path not in valid_class_paths:
            out(f"class '{klass}' has no path '{path}'", is_error=True)

    if level not in range(1, 21):
        out(f"level must be between 1-20 ({level})", is_error=True)

    if variant in ("false", "true"):
        if variant == "false" or race != "Human":
            variant = False
        else:
            variant = True
            out("variant rules are being used.", is_warning=True)
    else:
        out("argument variant must be 'false|true'", is_error=True)

    # Generate class features
    c = None
    t = None

    try:
        this_class = eval(klass)
        c = this_class(path, level)

        this_race = eval(race)
        t = this_race(subrace, c.features.get("abilities"), variant)
    except (
        ClassesInheritError,
        ClassesValueError,
        RacesInheritError,
        RacesValueError,
    ) as e:
        out(e, is_error=True)

    # Generate ability scores
    a = AttributeGenerator(c.features.get("abilities"))
    a.set_racial_bonus(race, subrace, c.features.get("abilities"), variant)

    # Generate character armor, tool and weapon proficiencies
    armors = None
    tools = None
    weapons = None

    try:
        armors = ProficiencyGenerator("armors", c.features, t.traits)
        tools = ProficiencyGenerator("tools", c.features, t.traits)
        weapons = ProficiencyGenerator("weapons", c.features, t.traits)
    except ValueError as e:
        out(str(e), is_error=True)

    # Generate character skills
    g = SkillGenerator(background, klass, t.traits.get("skills"))

    # Assign ability/feat improvements
    u = ImprovementGenerator(
        race=race,
        path=path,
        klass=klass,
        level=level,
        class_attr=c.features.get("abilities"),
        saves=c.features.get("saves"),
        spell_slots=c.features.get("spell_slots"),
        score_array=a.score_array,
        languages=t.traits.get("languages"),
        armor_proficiency=armors.proficiency,
        tool_proficiency=tools.proficiency,
        weapon_proficiency=weapons.proficiency,
        skills=g.skills,
        variant=variant,
    )

    # Create the data packet for the Writer
    proficiency_info = OrderedDict()
    proficiency_info["armors"] = u.armor_proficiency
    proficiency_info["tools"] = u.tool_proficiency
    proficiency_info["weapons"] = u.weapon_proficiency

    cs = OrderedDict()
    cs["race"] = race
    cs["subrace"] = subrace
    cs["sex"] = sex
    cs["background"] = background
    cs["class"] = klass
    cs["level"] = level
    cs["path"] = c.features.get("path")
    cs["bonus"] = get_proficiency_bonus(level)
    cs["score_array"] = u.score_array
    cs["saves"] = u.saves
    cs["spell_slots"] = c.features.get("spell_slots")
    cs["proficiency"] = proficiency_info
    cs["languages"] = u.languages
    cs["skills"] = u.skills
    cs["feats"] = u.feats
    cs["equipment"] = reader("backgrounds", (background, "equipment"))
    cs["features"] = c.features.get("features")
    cs["traits"] = t.traits

    try:
        with Writer(cs) as writer:
            writer.write(file)
    except (FileExistsError, IOError, OSError, TypeError, ValueError) as e:
        out(e, is_error=True)
    else:
        out(f"character saved to '{writer.save_path}'")


if __name__ == "__main__":
    main()
