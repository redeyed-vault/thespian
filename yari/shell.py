from collections import OrderedDict
from datetime import datetime
import os

from bs4 import BeautifulSoup
import click

from yari.generator import *
from yari.version import __version__
from yari.reader import reader


class Writer:
    """Responsible for writing XML character sheet from data."""

    def __init__(self, data: OrderedDict) -> None:
        """
        Args:
            data (OrderedDict): Character's detailed information.
        """
        # print(data)
        save_path = os.path.expanduser("~/Yari")
        if not os.path.exists(save_path):
            os.mkdir(save_path)
            raise FileNotFoundError(
                f"save directory '{save_path}' not found. Creating..."
            )

        if not isinstance(data, OrderedDict):
            raise TypeError("data argument must be of type 'OrderedDict'")

        data_keys = (
            "race",
            "background",
            "class",
            "score_array",
            "saves",
            "proficiency",
            "languages",
            "spell_slots",
            "skills",
            "feats",
            "equipment",
            "traits",
            "features",
        )
        if not all(k in data for k in data_keys):
            raise ValueError("data: all keys must have a value!")

        self.data = data
        self.save_path = save_path

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, traceback) -> None:
        pass

    def write(self, fp: str) -> None:
        """
        Args:
            fp (str): File to write character data to.
        """

        def format_ability_scores(abilities: OrderedDict) -> str:
            """Formats ability scores for character sheet.

            Args:
                abilities (OrderedDict): Character's ability scores.
            """
            ma = ""
            for ability, value_modifier in abilities.items():
                ability_array = (
                    ability,
                    value_modifier.get("Value"),
                    value_modifier.get("Modifier"),
                )
                ma += '<ability name="%s" value="%s" modifier="%s" />' % ability_array
            return ma

        def format_background(background: str) -> str:
            """Formats race for character sheet."""
            return f'<Background name="{background}" />'

        def format_class(class_: str, level: int, path: str) -> str:
            """Formats class for character sheet.

            Args:
                class_ (str): Character's chosen class.
                level (int): Character's level.
                path (str): Character's chosen archetype.
            """
            return f'<Class name="{class_}" level="{level}" path="{path}" />'

        def format_equipment(items: list) -> str:
            """Format equipment for character sheet.

            Args:
                items (list): Character's equipment list.
            """
            me = ""
            for item in items:
                me += f'<entry type="equipment" value="{item}" />'
            return me

        def format_feats(feats: list) -> str:
            """Formats feats for character sheet.

            Args:
                feats (list): Character's feat list.
            """
            mf = ""
            for feat in feats:
                mf += f'<entry type="feat" value="{feat}" />'
            return mf

        def format_features(class_: str, features: dict) -> str:
            """Formats class features for character sheet.

            Args:
                class_ (str): Character's chosen class.
                features (dict): Character's class features.
            """
            mf = ""
            for level, _features in features.items():
                for feature in _features:
                    mf += f'<entry level="{level}" name="{feature}" type="{class_} Class Feature" />'
            return mf

        def format_languages(languages: list) -> str:
            """Format languages for character sheet.

            Args:
                languages (list): Character's list of languages.
            """
            ml = ""
            for language in languages:
                ml += f'<entry type="language" value="{language}" />'
            return ml

        def format_proficiencies(proficiencies: OrderedDict) -> str:
            """Formats proficiencies for character sheet."""

            def ufirst(text: str):
                first_letter = text[0].upper()
                return f"{first_letter}{text[1:len(text)]}"

            mp = ""
            for type, proficiency_list in proficiencies.items():
                mp += f"<{ufirst(type)}>"
                for proficiency in proficiency_list:
                    mp += f'<entry type="proficiency" value="{proficiency}" />'
                mp += f"</{type}>"
            return mp

        def format_race(race: str, subrace: str, sex: str) -> str:
            """Formats race for character sheet."""
            return f'<Race name="{race}" subrace="{subrace}" sex="{sex}" />'

        def format_saving_throws(saves: list) -> str:
            """Formats saves for character sheet."""
            ms = ""
            for save_array in saves:
                ms += '<entry ability="%s" type="save" value="%s" />' % save_array
            return ms

        def format_skills(skills: list) -> str:
            """Formats skills for character sheet."""
            ms = ""
            for skill_array in skills:
                ms += '<entry name="%s" modifier="%s" />' % skill_array
            return ms

        def format_traits(traits: dict, race: str, subrace=None) -> str:
            """Formats trait values for character sheet."""
            if subrace is not None:
                trait_label = f"{subrace} {race} Trait"
            elif race in ("HalfElf", "HalfOrc",):
                if race == "HalfElf":
                    trait_label = "Half-elf Trait"
                else:
                    trait_label = "Half-orc Trait"
            else:
                trait_label = f"{race} Trait"

            mt = ""
            for trait, values in traits.items():
                if trait in ("abilities", "languages", "skills"):
                    continue
                elif trait == "ancestry":
                    dragon_ancestry = traits.get(trait)
                    mt += '<entry name="Draconic Ancestry" type="{}" value="{}" />'.format(
                        trait_label, dragon_ancestry
                    )
                    mt += '<entry name="Breath Weapon" type="{}" value="{}" />'.format(
                        trait_label, dragon_ancestry
                    )
                elif trait == "cantrip":
                    if subrace == "High":
                        mt += '<entry name="Cantrip" type="{}" values="{}" />'.format(
                            trait_label, ",".join(values)
                        )
                elif trait == "darkvision":
                    darkvision_type = "Darkvision"
                    if traits.get(trait) > 60:
                        darkvision_type = "Superior Darkvision"
                    mt += '<entry name="{}" range="{}" type="{}" />'.format(
                        darkvision_type, traits.get(trait), trait_label
                    )
                elif trait == "magic":
                    magic_name = None
                    if race == "Aasimar":
                        magic_name = "Celestial Legacy"
                    elif subrace == "Drow":
                        magic_name = "Drow Magic"
                    elif subrace == "Duergar":
                        magic_name = "Duergar Magic"

                    for level, spell in traits[trait].items():
                        if isinstance(spell, list):
                            spell = ", ".join(spell)
                        mt += '<entry name="{}" level="{}" spell="{}" type="{}" />'.format(
                            magic_name, level, spell, trait_label
                        )
                elif trait == "proficiency":
                    proficiency_list = traits.get(trait)
                    for proficiency_type in proficiency_list:
                        if proficiency_type == "armors":
                            armors = proficiency_list.get(proficiency_type)
                            mt += '<entry name="Dwarven Armor Training" type="{}" values="{}" />'.format(
                                trait_label, ", ".join(armors)
                            )

                        if proficiency_type == "tools":
                            tools = proficiency_list.get(proficiency_type)
                            mt += '<entry name="Tool Proficiency" type="{}" values="{}" />'.format(
                                trait_label, ", ".join(tools)
                            )

                        if proficiency_type == "weapons":
                            proficiency_title = None
                            if race == "Dwarf":
                                proficiency_title = "Dwarven Combat"
                            elif subrace is not None:
                                if subrace in ("Eladrin", "High", "Wood",):
                                    proficiency_title = "Elf Weapon"
                                elif subrace == "Drow":
                                    proficiency_title = "Drow Weapon"
                                elif subrace == "Sea":
                                    proficiency_title = "Sea Elf"
                            weapons = proficiency_list.get(proficiency_type)
                            mt += '<entry name="{} Training" type="{}" values="{}" />'.format(
                                proficiency_title, trait_label, ", ".join(weapons)
                            )
                elif trait == "resistance":
                    # Celestial Resistance
                    if race == "Aasimar":
                        mt += f'<entry name="Celestial Resistance" type="{trait_label}" values="Necrotic, Radiant" />'
                    # Dragonborn Damage Resistance
                    elif race == "Dragonborn":
                        mt += '<entry name="Damage Resistance" type="{}" values="{}" />'.format(
                            trait_label, ",".join(values)
                        )
                    # Dwarf Resilience
                    elif race == "Dwarf":
                        mt += f'<entry name="Dwarven Resilience" type="{trait_label}" values="Poison" />'
                    # Elf/Half-Elf Fey Ancestry
                    elif race in ("Elf", "HalfElf",):
                        mt += f'<entry name="Fey Ancestry" type="{trait_label}" values="Charm, Sleep" />'
                    # Duergar/Stout Halfling Resilience
                    elif subrace in ("Duergar", "Stout",):
                        if subrace == "Duergar":
                            mt += f'<entry name="Duergar Resilience" type="{trait_label}" values="Charm, Illusion, Paralysis" />'
                        elif subrace == "Stout":
                            mt += f'<entry name="Stout Resilience" type="{trait_label}" values="Poison" />'
                    # Shadar-kai Resistance
                    elif subrace == "Shadar-kai":
                        mt += f'<entry name="Necrotic Resistance" type="{trait_label}" values="Necrotic" />'
                # Drow/Duergar have sensitivity to sunlight
                elif trait == "sensitivity":
                    if subrace is not None and subrace in ("Drow", "Duergar"):
                        mt += f'<entry name="Sunlight Sensitivity" type="{trait_label}" />'
                elif trait == "stealthy":
                    mt += f'<entry name="Naturally Stealthy" type="{trait_label}" />'
                elif trait == "toughness":
                    mt += f'<entry name="Toughness" type="{trait_label}" />'
                elif trait == "trance":
                    mt += f'<entry name="Trance" type="{trait_label}" />'
            return mt

        self.save_path = os.path.join(self.save_path, f"{fp}.xml")
        if os.path.exists(self.save_path):
            raise FileExistsError(f"character save '{self.save_path}' already exists.")

        with open(self.save_path, "w+") as cs:
            now = datetime.now()
            timestamp = datetime.fromtimestamp(datetime.timestamp(now))
            x = '<?xml version="1.0"?><Writer created="{}" version="{}">'.format(
                timestamp, __version__
            )
            x += format_race(
                self.data.get("race").get("race"),
                self.data.get("race").get("subrace"),
                self.data.get("race").get("sex"),
            )
            x += format_background(self.data.get("background"))
            x += format_class(
                self.data.get("class").get("class"),
                self.data.get("class").get("level"),
                self.data.get("class").get("archetype"),
            )
            x += "<AbilityScores>"
            x += format_ability_scores(self.data.get("score_array"))
            x += "</AbilityScores>"
            x += '<Spell slots="{}" />'.format(self.data.get("spell_slots"))
            x += "<Proficiencies>"
            x += '<Proficiency bonus="{}" />'.format(
                self.data.get("class").get("proficiency")
            )
            x += format_proficiencies(self.data.get("proficiency"))
            x += "<Languages>"
            x += format_languages(self.data.get("languages"))
            x += "</Languages><SavingThrows>"
            x += format_saving_throws(self.data.get("saves"))
            x += "</SavingThrows><Skills>"
            x += format_skills(self.data.get("skills"))
            x += "</Skills></Proficiencies><Feats>"
            x += format_feats(self.data.get("feats"))
            x += "</Feats><Equipment>"
            x += format_equipment(self.data.get("equipment"))
            x += "</Equipment><Traits>"
            x += format_traits(
                self.data.get("traits"),
                self.data.get("race").get("race"),
                self.data.get("race").get("subrace"),
            )
            x += "</Traits><Features>"
            x += format_features(
                self.data.get("class").get("class"), self.data.get("features")
            )
            x += "</Features></Writer>"
            cs.write(BeautifulSoup(x, "xml").prettify())
        cs.close()


@click.command()
@click.option("-file", default="", help="Character sheet file name.", type=str)
@click.option("-race", default="Human", help="Character's chosen race.", type=str)
@click.option("-subrace", default="", help="Character's chosen subrace.", type=str)
@click.option("-sex", default="", help="Character's chosen gender.", type=str)
@click.option(
    "-background", default="", help="Character's chosen background.", type=str
)
@click.option(
    "-klass", default="Barbarian", help="Character's chosen class.", type=str,
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
    def _done(message: str) -> None:
        click.secho(f"success: {message}", bold=True, fg="bright_green")

    def _error(message: str) -> None:
        click.secho(f"error: {message}", bold=True, err=True, fg="red")
        exit()

    def _warn(message: str) -> None:
        click.secho(f"warning: {message}", bold=True, fg="yellow")

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
        if race not in tuple(reader("races").keys()):
            _error(f"invalid character race '{race}'")

    if subrace == "":
        subrace = None
    else:
        try:
            valid_subraces = get_subraces_by_race(race)
            if len(valid_subraces) is 0:
                raise ValueError(f"race '{race}' has no available subraces")

            if subrace not in valid_subraces:
                raise ValueError(f"invalid subrace race '{subrace}'")
        except ValueError as error:
            out(error, is_error=True)

    the_sexes = ["Female", "Male"]
    if sex in the_sexes:
        sex = sex
    else:
        sex = random.choice(the_sexes)

    if background == "":
        background = reader("classes", (klass, "background"))
    else:
        valid_backgrounds = tuple(reader("backgrounds").keys())
        if background not in valid_backgrounds:
            out(f"invalid character background '{background}'", is_error=True)

    if klass != "":
        try:
            if klass not in tuple(reader("classes").keys()):
                raise ValueError
        except ValueError:
            out(f"invalid character class '{klass}'", is_error=True)

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
    try:
        this_class = eval(klass)
        c = this_class(level=level, path=path)
        this_race = eval(race)
        t = this_race(
            class_attr=c.features.get("abilities"), subrace=subrace, variant=variant
        )
    except (Exception, ValueError) as e:
        out(e, is_error=True)

    # Generate ability scores
    a = AbilityScoreGenerator(
        race=race,
        class_attr=c.features.get("abilities"),
        variant=variant,
        subrace=subrace,
    )

    # Generate character armor, tool and weapon proficiencies
    try:
        armors = ProficiencyGenerator("armors", c.features, t.traits)
        tools = ProficiencyGenerator("tools", c.features, t.traits)
        weapons = ProficiencyGenerator("weapons", c.features, t.traits)
    except ValueError as e:
        out(e, is_error=True)

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

    cs = OrderedDict()
    race_info = OrderedDict()
    race_info["race"] = race
    race_info["subrace"] = subrace
    race_info["sex"] = sex
    cs["race"] = race_info
    cs["background"] = background
    class_info = OrderedDict()
    class_info["class"] = klass
    class_info["level"] = level
    class_info["archetype"] = c.features.get("path")
    class_info["proficiency"] = get_proficiency_bonus(level)
    cs["class"] = class_info
    cs["score_array"] = u.score_array
    cs["saves"] = u.expand_saving_throws()
    cs["spell_slots"] = c.features.get("spell_slots")
    proficiency_info = OrderedDict()
    proficiency_info["armors"] = u.armor_proficiency
    proficiency_info["tools"] = u.tool_proficiency
    proficiency_info["weapons"] = u.weapon_proficiency
    cs["proficiency"] = proficiency_info
    cs["languages"] = u.languages
    cs["skills"] = expand_skills(u.skills, u.score_array)
    cs["feats"] = u.feats
    cs["equipment"] = reader("backgrounds", (background, "equipment"))
    cs["features"] = c.features.get("features")
    cs["traits"] = t.traits

    try:
        with Writer(cs) as writer:
            if file == "":
                writer.write(str(datetime.timestamp(datetime.now())))
            else:
                writer.write(file)
    except (FileExistsError, FileNotFoundError, TypeError) as e:
        out(e, is_error=True)
    else:
        out(f"character saved to '{writer.save_path}'")


if __name__ == "__main__":
    main()
