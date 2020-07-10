from collections import OrderedDict

import click

from yari.classes import *
from yari.attributes import AttributeGenerator
from yari.exceptions import RatioValueError
from yari.improvement import ImprovementGenerator
from yari.proficiency import ProficiencyGenerator, ProficiencyTypeValueError
from yari.races import *
from yari.ratio import RatioGenerator
from yari.skills import SkillGenerator
from yari.version import __version__
from yari.yaml import _read
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
    "(Lightfoot, Stout).",
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
    "(The Archfey, The Fiend, The Great Old One, and Wizard (School of "
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

    if variant in ("false", "true"):
        if variant == "false" or race != "Human":
            variant = False
        else:
            variant = True
            out("variant rules are being used.", is_warning=True)
    else:
        out("argument variant must be 'false|true'", is_error=True)

    # Generate class features and racial traits.
    def callback(method, **kw):
        def init():
            call_class = eval(method)
            if "path" and "level" in kw:
                return call_class(kw["path"], kw["level"])
            elif "subrace" and "class_attr" and "variant" in kw:
                return call_class(kw["subrace"], kw["class_attr"], kw["variant"])
            else:
                raise RuntimeError(f"Invalid callback {method}")

        return init()

    try:
        cg = callback(klass, path=path, level=level)
        features = cg.features
        rg = callback(
            race,
            subrace=subrace,
            class_attr=features.get("abilities"),
            variant=variant,
        )

        def trait_filter(base_traits: dict, base_level: int) -> dict:
            """Removes traits character does not have level requirements for."""
            if "magic" in base_traits:
                magic_traits = dict()
                for magic_level, spell in base_traits["magic"].items():
                    if magic_level <= base_level:
                        magic_traits[magic_level] = spell
                base_traits["magic"] = magic_traits
            return base_traits

        traits = trait_filter(rg.traits, level)

        # Generate ability scores.
        ag = AttributeGenerator(features.get("abilities"))
        ag.set_racial_bonus(race, subrace, features.get("abilities"), variant)
        score_array = ag.score_array

        # Generate character armor, tool and weapon proficiencies.
        armors = ProficiencyGenerator("armors", features, traits).proficiency
        tools = ProficiencyGenerator("tools", features, traits).proficiency
        weapons = ProficiencyGenerator("weapons", features, traits).proficiency

        # Generate character skills.
        skills = SkillGenerator(background, klass, traits.get("skills")).skills

        # Assign ability/feat improvements.
        u = ImprovementGenerator(
            race=race,
            path=path,
            klass=klass,
            level=level,
            class_attr=features.get("abilities"),
            saves=features.get("saves"),
            spell_slots=features.get("spell_slots"),
            score_array=score_array,
            languages=traits.get("languages"),
            armor_proficiency=armors,
            tool_proficiency=tools,
            weapon_proficiency=weapons,
            skills=skills,
            variant=variant,
        )

        # Create proficiency data packet.
        proficiency_info = OrderedDict()
        proficiency_info["armors"] = u.armor_proficiency
        proficiency_info["tools"] = u.tool_proficiency
        proficiency_info["weapons"] = u.weapon_proficiency

        # Calculate character height/weight.
        try:
            mg = RatioGenerator(race, subrace, sex)
            ratio = mg.calculate()
            height = f"{ratio[0][0]}' {ratio[0][1]}\""
            weight = ratio[1]
        except RatioValueError as e:
            out(str(e), is_error=True)
        else:
            # Gather data for character sheet.
            cs = OrderedDict()
            cs["race"] = u.race
            cs["subrace"] = subrace
            cs["sex"] = sex
            cs["background"] = background
            cs["height"] = height
            cs["weight"] = weight
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
            cs["features"] = features.get("features")
            cs["traits"] = traits

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
