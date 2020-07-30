from collections import OrderedDict

import click

from yari.classes import *
from yari.attributes import AttributeGenerator
from yari.improvement import ImprovementGenerator
from yari.loader import _read
from yari.proficiency import ProficiencyGenerator, ProficiencyTypeValueError
from yari.races import *
from yari.version import __version__
from yari.writer import Writer


@click.command()
@click.option(
    "-file",
    default="",
    help="File name to write character to.",
    required=True,
    type=str,
)
@click.option(
    "-race",
    default="",
    help="Character's chosen race. Available races are: Aasimar, Dragonborn, "
    "Dwarf, Elf, Gith, Gnome, HalfElf, HalfOrc, Halfling, Human and Tiefling.",
    type=str,
)
@click.option(
    "-subrace",
    default="",
    help="Character's chosen subrace. Available subraces are based upon the "
    "chosen race: Aasimar (Fallen, Protector, Scourge), Dwarf (Duergar, Hill, "
    "Mountain), Elf (Drow, Eladrin, High, Sea, Shadar-kai, Wood), "
    "Gith (Githyanki, Githzerai), Gnome (Deep, Forest, Rock), Halfling "
    "(Lightfoot, Stout), Tiefling (Asmodeus, Baalzebub, Dispater, Fierna, "
    "Glasya, Levistus, Mammon, Mephistopheles, Zariel).",
    type=str,
)
@click.option("-sex", default="", help="Character's chosen gender.", type=str)
@click.option(
    "-background",
    default="",
    help="Character's chosen background. Available backgrounds are: Acolyte, "
    "Charlatan, Criminal, Entertainer, Folk Hero, Guild Artisan, Hermit, Noble, "
    "Outlander, Sage, Sailor, Soldier, Urchin",
    type=str,
)
@click.option(
    "-klass",
    default="",
    help="Character's chosen class. Available classes are: Barbarian, Bard, "
    "Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, "
    "Warlock, and Wizard.",
    type=str,
)
@click.option(
    "-path",
    default="",
    help="Character's chosen path (archetype, domain, path, etc). Available "
    "paths are based upon the chosen class: Barbarian (Path of the Berserker, "
    "Path of the Totem Warrior), Bard (College of Lore, College of Valor), "
    "Cleric (Knowledge Domain, Life Domain, Light Domain, Nature Domain, "
    "Tempest Domain, Trickery Domain, War Domain), Druid (Circle of the Arctic, "
    "Circle of the Coast, Circle of the Desert, Circle of the Forest, Circle "
    "of the Grassland, Circle of the Moon, Circle of the Mountain, Circle of "
    "the Swamp, Circle of the Underdark), Fighter (Battle Master, Champion, "
    "Eldritch Knight), Monk (Way of Shadow, Way of the Four Elements, Way of "
    "the Open Hand), Paladin (Oath of the Ancients, Oath of Devotion, Oath of "
    "Vengeance), Ranger (Beast Master, Hunter), Rogue (Arcane Trickster, "
    "Assassin, Thief), Sorcerer (Draconic Bloodline, Wild Magic), Warlock "
    "(The Archfey, The Fiend, The Great Old One), and Wizard (School of "
    "Abjuration, School of Conjuration, School of Divination, School of "
    "Enchantment, School of Evocation, School of Illusion, School of "
    "Necromancy, School of Transmutation).",
    type=str,
)
@click.option(
    "-level",
    default=1,
    help="Character's class level. Must be at or inbetween 1 and 20.",
    type=int,
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
) -> None:
    def out(message: str, **kw):
        if "is_error" in kw and kw["is_error"]:
            click.secho(f"error: {message}", bold=True, fg="red")
            exit()
        elif "is_warning" in kw and kw["is_warning"]:
            click.secho(f"warning: {message}", bold=True, fg="yellow")
        else:
            click.secho(f"success: {message}", bold=True, fg="bright_green")

    # Handle application argument processing.
    if file == "":
        out("character must have a file name", is_error=True)

    if race != "":
        if race not in _read(file="races"):
            out(f"invalid character race '{race}'", is_error=True)
    else:
        race = random.choice(_read(file="races"))

    valid_subraces = [sr for sr in get_subraces_by_race(race)]
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

    the_sexes = ("Female", "Male")
    if sex in the_sexes:
        sex = sex
    else:
        sex = random.choice(the_sexes)

    if klass == "":
        klass = random.choice(_read(file="classes"))
    else:
        try:
            if klass not in _read(file="classes"):
                raise ValueError
        except ValueError:
            out(f"invalid character class '{klass}'", is_error=True)

    if background == "":
        background = _read(klass, "background", file="classes")
    else:
        valid_backgrounds = _read(file="backgrounds")
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

    # Generate class features and racial traits.
    def callback(method, **kw):
        def init():
            call_class = eval(method)
            if all(k in kw for k in ("path", "level", "race_skills")):
                return call_class(kw["path"], kw["level"], kw["race_skills"])
            elif all(k in kw for k in ("subrace", "sex", "level",)):
                return call_class(kw["subrace"], kw["sex"], kw["level"])
            else:
                raise RuntimeError(f"Invalid callback '{method}' specified.")

        return init()

    try:
        # Racial traits
        rg = callback(race, subrace=subrace, sex=sex, level=level,)

        # Class features
        cg = callback(klass, path=path, level=level, race_skills=rg.skills)

        # Generate ability scores.
        ag = AttributeGenerator(cg.primary_ability, rg.bonus)
        score_array = ag.score_array

        # Generate character armor, tool and weapon proficiencies.
        armors = ProficiencyGenerator("armors", cg.armors, rg.armors).proficiency
        tools = ProficiencyGenerator("tools", cg.tools, rg.tools).proficiency
        weapons = ProficiencyGenerator("weapons", cg.weapons, rg.weapons).proficiency

        # Assign ability/feat improvements.
        u = ImprovementGenerator(
            race=race,
            path=path,
            klass=klass,
            level=level,
            primary_ability=cg.primary_ability,
            saves=cg.saving_throws,
            spell_slots=cg.spell_slots,
            score_array=score_array,
            languages=rg.languages,
            armor_proficiency=armors,
            tool_proficiency=tools,
            weapon_proficiency=weapons,
            skills=cg.skills,
        )

        # Create proficiency data packet.
        proficiency_info = OrderedDict()
        proficiency_info["armors"] = u.armor_proficiency
        proficiency_info["tools"] = u.tool_proficiency
        proficiency_info["weapons"] = u.weapon_proficiency

        # Gather data for character sheet.
        cs = OrderedDict()
        cs["race"] = u.race
        cs["subrace"] = subrace
        cs["sex"] = sex
        cs["background"] = background
        cs["size"] = rg.size
        cs["class"] = klass
        cs["level"] = level
        cs["path"] = u.path
        cs["bonus"] = get_proficiency_bonus(level)
        cs["score_array"] = u.score_array
        cs["saves"] = u.saves
        cs["spell_slots"] = u.spell_slots
        cs["proficiency"] = proficiency_info
        cs["languages"] = u.languages
        cs["skills"] = u.skills
        cs["feats"] = u.feats
        cs["equipment"] = _read(background, "equipment", file="backgrounds")
        cs["features"] = cg.features
        cs["traits"] = rg.other

        try:
            with Writer(cs) as writer:
                writer.write(file)
        except (FileExistsError, IOError, OSError, TypeError, ValueError) as e:
            out(e, is_error=True)
        else:
            out(f"character saved to '{writer.save_path}'")
    except (
        NameError,
        RuntimeError,
        InheritanceError,
        InvalidValueError,
        ProficiencyTypeValueError,
    ) as e:
        out(e, is_error=True)


if __name__ == "__main__":
    main()
