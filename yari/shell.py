from collections import OrderedDict
from datetime import datetime
import os

from bs4 import BeautifulSoup
import click

from yari.classes import *
from yari.attributes import (
    AttributeGenerator,
    Charisma,
    Constitution,
    Dexterity,
    Intelligence,
    Strength,
    Wisdom,
)
from yari.generator import (
    ImprovementGenerator,
    ProficiencyGenerator,
    SkillGenerator,
)
from yari.races import *
from yari.version import __version__
from yari.reader import reader


class Writer:
    """Handles the writing of the character sheet."""

    def __init__(self, data: OrderedDict) -> None:
        """
        Args:
            data (OrderedDict): Character's information packet.
        """
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
            "subrace",
            "sex",
            "background",
            "class",
            "level",
            "path",
            "bonus",
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

        def format_ability(attributes: dict):
            """Formats ability scores and associated ability check values."""
            block = '<ability label="{}" value="{}" modifier="{}">'.format(
                attributes.get("name"),
                attributes.get("value"),
                attributes.get("modifier"),
            )
            for index, value in attributes.items():
                if index == "ability_checks":
                    block += f'<entry label="Ability Checks" value="{value}"/>'
                if index == "saving_throws":
                    block += f'<entry label="Saving Throws" value="{value}"/>'
                if index == "skills":
                    if len(value) is not 0:
                        for skill, modifier in value.items():
                            block += f'<entry label="{skill} Skill Checks" value="{modifier}"/>'
                if index == "carry_capacity":
                    block += f'<entry label="Carry Capacity" values="{value}"/>'
                if index == "push_pull_carry":
                    block += (
                        f'<entry label="Push Pull Carry Capacity" values="{value}"/>'
                    )
                if index == "maximum_lift":
                    block += f'<entry label="Maximum Lift Capacity" values="{value}"/>'
            block += "</{}>".format(attributes.get("name"))
            return block

        def format_equipment(items: list) -> str:
            """Format equipment for character sheet.

            Args:
                items (list): Character's equipment list.
            """
            block = ""
            for item in items:
                block += f'<entry label="equipment" value="{item}" />'
            return block

        def format_feats(feats: list) -> str:
            """Formats feats for character sheet.

            Args:
                feats (list): Character's feat list.
            """
            block = ""
            for feat in feats:
                block += f'<entry label="feat" value="{feat}" />'
            return block

        def format_features(class_: str, features: dict) -> str:
            """Formats class features for character sheet.

            Args:
                class_ (str): Character's chosen class.
                features (dict): Character's class features.
            """
            block = ""
            for level, _features in features.items():
                for feature in _features:
                    block += f'<entry label="{class_} Class Feature" level="{level}" name="{feature}" />'
            return block

        def format_languages(languages: list) -> str:
            """Format languages for character sheet.

            Args:
                languages (list): Character's list of languages.
            """
            block = ""
            for language in languages:
                block += f'<entry label="language" value="{language}" />'
            return block

        def format_proficiencies(proficiencies: OrderedDict) -> str:
            """Formats proficiencies for character sheet."""
            block = ""
            for type, proficiency_list in proficiencies.items():
                block += f"<{type}>"
                for proficiency in proficiency_list:
                    block += f'<entry label="proficiency" value="{proficiency}" />'
                block += f"</{type}>"
            return block

        def format_saving_throws(saves: list) -> str:
            """Formats saves for character sheet."""
            block = ""
            for save in saves:
                block += '<entry label="save" value="%s" />' % save
            return block

        def format_skills(skills: list) -> str:
            """Format skills for character sheet.

            Args:
                skills (list): Character's list of skills.
            """
            block = ""
            for skill in skills:
                block += f'<entry label="skill" value="{skill}" />'
            return block

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

        now = datetime.now()
        timestamp = datetime.fromtimestamp(datetime.timestamp(now))

        if self.data.get("subrace") is not None:
            race = f'{self.data.get("race")}, {self.data.get("subrace")}'
        else:
            race = self.data.get("race")

        score_array = self.data.get("score_array")
        strength = Strength(score_array.get("Strength"), self.data.get("skills"))
        dexterity = Dexterity(score_array.get("Dexterity"), self.data.get("skills"))
        constitution = Constitution(
            score_array.get("Constitution"), self.data.get("skills")
        )
        intelligence = Intelligence(
            score_array.get("Intelligence"), self.data.get("skills")
        )
        wisdom = Wisdom(score_array.get("Wisdom"), self.data.get("skills"))
        charisma = Charisma(score_array.get("Charisma"), self.data.get("skills"))

        x = '<?xml version="1.0"?><yari>'
        x += f"<meta><created>{timestamp}</created>"
        x += f"<version>{__version__}</version></meta>"
        x += f"<character><race>{race}</race>"
        x += f'<sex>{self.data.get("sex")}</sex>'
        x += f'<background>{self.data.get("background")}</background>'
        x += f'<class>{self.data.get("class")}</class>'
        x += f'<level>{self.data.get("level")}</level>'
        x += f'<path>{self.data.get("path")}</path>'
        x += "<ability_scores>"
        x += format_ability(strength.attr)
        x += format_ability(dexterity.attr)
        x += format_ability(constitution.attr)
        x += format_ability(intelligence.attr)
        x += format_ability(wisdom.attr)
        x += format_ability(charisma.attr)
        x += "</ability_scores>"
        x += f'<spell_slots>{self.data.get("spell_slots")}</spell_slots>'
        x += "<proficiencies>"
        x += f'<proficiency>{self.data.get("bonus")}</proficiency>'
        x += format_proficiencies(self.data.get("proficiency"))
        x += f'<languages>{format_languages(self.data.get("languages"))}</languages>'
        x += "<saving_throws>"
        x += format_saving_throws(self.data.get("saves"))
        x += "</saving_throws><skills>"
        x += format_skills(self.data.get("skills"))
        x += "</skills></proficiencies><feats>"
        x += format_feats(self.data.get("feats"))
        x += "</feats><equipment>"
        x += format_equipment(self.data.get("equipment"))
        x += "</equipment><traits>"
        x += format_traits(
            self.data.get("traits"), self.data.get("race"), self.data.get("subrace"),
        )
        x += "</traits><features>"
        x += format_features(self.data.get("class"), self.data.get("features"))
        x += "</features></character></yari>"
        x = BeautifulSoup(x, "xml").prettify()

        with open(self.save_path, "w+") as cs:
            cs.write(x)
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
            out(f"invalid character race '{race}'", is_error=True)

    if subrace == "":
        subrace = None
    else:
        try:
            valid_subraces = get_subraces_by_race(race)
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
    c = None
    t = None

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
    a = AttributeGenerator(c.features.get("abilities"))
    a.set_racial_bonus(
        race=race,
        subrace=subrace,
        class_attr=c.features.get("abilities"),
        variant=variant,
    )

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
    proficiency_info = OrderedDict()
    proficiency_info["armors"] = u.armor_proficiency
    proficiency_info["tools"] = u.tool_proficiency
    proficiency_info["weapons"] = u.weapon_proficiency
    cs["proficiency"] = proficiency_info
    cs["languages"] = u.languages
    cs["skills"] = u.skills
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
