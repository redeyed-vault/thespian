from collections import OrderedDict
import traceback

import click

from yari.classes import *
from yari.attributes import AttributeGenerator
from yari.improvement import ImprovementGenerator
from yari.proficiency import ProficiencyGenerator
from yari.races import *
from yari.server import CharacterServer
from yari.version import __version__


@click.command()
@click.option(
    "-race",
    default="Human",
    help="Character's chosen race. Available races are: Aasimar, Bugbear, "
    "Dragonborn, Dwarf, Elf, Firbolg, Gith, Gnome, Goblin, Goliath, HalfElf, "
    "HalfOrc, Halfling, Hobgoblin, Human, Kenku, Kobold, Lizardfolk, Orc, "
    "Tabaxi, Tiefling, Triton and Yuanti. Default value is 'Human'.",
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
    "-alignment",
    default="N",
    help="Character's chosen alignment. Available alignments are: CE, CG, CN, "
    "LE, LG, LN, NE, NG, N. Default value is 'N'.",
    type=str,
)
@click.option(
    "-background",
    default="",
    help="Character's chosen background. Available backgrounds are: Acolyte, "
    "Charlatan, Criminal, Entertainer, Folk Hero, Guild Artisan, Hermit, Noble, "
    "Outlander, Sage, Sailor, Soldier, Urchin.",
    type=str,
)
@click.option(
    "-klass",
    default="Fighter",
    help="Character's chosen class. Available classes are: Barbarian, Bard, "
    "Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, "
    "Warlock, and Wizard. Default value is 'Fighter'.",
    type=str,
)
@click.option(
    "-subclass",
    default="",
    help="Character's chosen subclass (archetype, domain, path, etc). Available "
    "subclasses are based upon the chosen class: Barbarian (Path of the Berserker, "
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
    help="Character's class level. Must be between 1-20. Default value is 1.",
    type=int,
)
@click.option(
    "-ratio",
    default=5,
    help="Character's 'ability to feat' upgrade ratio. Must be between 0-10. "
    "This value will determine the percentage of level upgrades allocated to "
    "the character's ability scores. The difference between this value from "
    "100 will then be allocated to the percentage of chosen feats (i.e: So if "
    "this value is 2 or 20%, 80 percent will automatically be allocated to feats). "
    "Default value is 5.",
    type=int,
)
@click.option(
    "-port",
    default=8080,
    help="Character server's chosen port. Default value is 8080.",
    type=int,
)
@click.version_option(prog_name="Yari", version=__version__)
def main(
    race: str,
    subrace: str,
    sex: str,
    alignment: str,
    background: str,
    klass: str,
    subclass: str,
    level: int,
    ratio: int,
    port: int,
) -> None:
    def callback(method: str, **kw):
        def init():
            call_class = eval(method)
            if all(k in kw for k in ("subclass", "background", "level", "race_skills")):
                return call_class(
                    kw["subclass"], kw["background"], kw["level"], kw["race_skills"]
                )
            elif all(
                k in kw
                for k in (
                    "sex",
                    "subrace",
                    "level",
                )
            ):
                return call_class(kw["sex"], kw["subrace"], kw["level"])
            else:
                raise RuntimeError(
                    f"Not all parameters specified for callback '{method}'."
                )

        return init()

    def out(message: str, output_code: int = 0):
        if output_code not in range(-1, 3):
            raise ValueError("Argument 'output_code' is invalid.")
        else:
            if output_code in (1, 2):
                click.secho(f"error: {message}", bold=True, fg="red")
                if output_code == 2:
                    traceback.print_exc()
                exit()
            elif output_code == -1:
                click.secho(f"warning: {message}", bold=True, fg="yellow")
            else:
                click.secho(f"success: {message}", fg="bright_green")

    # Handle application argument processing.
    if race not in ALLOWED_PC_RACES:
        out(f"invalid character race '{race}'.", 1)

    if klass not in ALLOWED_PC_CLASSES:
        out(f"invalid character class '{klass}'", 1)

    if level not in range(1, 21):
        out(f"level must be between 1-20 ({level})", 1)

    if ratio not in range(0, 11):
        out(f"ratio must be between 0-10 ({ratio})", 1)
    else:
        ratios = {
            0: 0,
            1: 10,
            2: 20,
            3: 30,
            4: 40,
            5: 50,
            6: 60,
            7: 70,
            8: 80,
            9: 90,
            10: 100,
        }
        ratio = ratios.get(ratio)

    alignments = {
        "CE": "Chaotic Evil",
        "CG": "Chaotic Good",
        "CN": "Chaotic Neutral",
        "LE": "Lawful Evil",
        "LG": "Lawful Good",
        "LN": "Lawful Neutral",
        "NE": "Neutral Evil",
        "NG": "Neutral Good",
        "N": "True Neutral",
    }
    if alignment not in alignments:
        out(f"invalid character alignment '{alignment}'.", 1)
    else:
        alignment = alignments.get(alignment)

    rg = None
    try:
        if sex in ALLOWED_PC_GENDERS:
            sex = sex
        else:
            sex = random.choice(ALLOWED_PC_GENDERS)

        subraces_by_race = [s for s in get_subraces_by_race(ALLOWED_PC_SUBRACES, race)]
        if subrace == "":
            if len(subraces_by_race) != 0:
                subrace = random.choice(subraces_by_race)
        else:
            try:
                if len(subraces_by_race) == 0:
                    raise ValueError(f"race '{race}' has no available subraces")

                if subrace not in subraces_by_race:
                    raise ValueError(f"invalid subrace race '{subrace}'")
            except ValueError as e:
                out(str(e), 1)

        rg = callback(race, sex=sex, level=level, subrace=subrace)
    except (
        Exception,
        NameError,
        ValueError,
    ) as race_error:
        out(race_error, 2)

    cg = None
    try:
        if background == "":
            background = get_default_background(klass)
        else:
            if background not in ALLOWED_PC_BACKGROUNDS:
                out(f"invalid character background '{background}'", 1)

        valid_class_subclasses = get_subclasses_by_class(klass)
        if subclass == "":
            subclass = random.choice(valid_class_subclasses)
        else:
            if subclass not in valid_class_subclasses:
                out(f"class '{klass}' has no subclass '{subclass}'", 1)

        cg = callback(
            klass,
            background=background,
            subclass=subclass,
            level=level,
            race_skills=rg.skills,
        )
    except (
        Exception,
        NameError,
        ValueError,
    ) as class_error:
        out(class_error, 2)

    try:
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
            subrace=subrace,
            subclass=subclass,
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
            feats=[],
            upgrade_ratio=ratio,
        )
        u.upgrade()

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
        cs["alignment"] = alignment
        cs["background"] = background
        cs["size"] = rg.size
        cs["class"] = klass
        cs["level"] = level
        cs["subclass"] = u.subclass
        cs["bonus"] = get_proficiency_bonus(level)
        cs["score_array"] = u.score_array
        cs["saves"] = u.saves
        cs["spell_slots"] = u.spell_slots
        cs["proficiency"] = proficiency_info
        cs["languages"] = u.languages
        cs["skills"] = u.skills
        cs["feats"] = u.feats
        cs["equipment"] = cg.equipment
        cs["features"] = cg.features
        cs["traits"] = rg.other

        try:
            with CharacterServer(cs) as w:
                w.run(port)
        except (OSError, TypeError, ValueError) as e:
            out(e, 2)
    except ValueError as error:
        out(str(error), 2)


if __name__ == "__main__":
    main()
