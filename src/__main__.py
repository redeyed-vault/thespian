from collections import OrderedDict
from dataclasses import dataclass
import math
import random
import socket
import sys
import traceback

from aiohttp import web
from bs4 import BeautifulSoup
import click

from . import __version__
from .dice import roll
from .yaml import load


ALLOWED_PC_BACKGROUNDS = load(file="classes")
ALLOWED_PC_CLASSES = load(file="classes")
ALLOWED_PC_SUBCLASSES = load(file="subclasses")

ALLOWED_PC_GENDERS = ("Female", "Male")
ALLOWED_PC_RACES = load(file="races")
ALLOWED_PC_SUBRACES = load(file="subraces")


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
    help="Character's chosen alignment. Available alignments are: CE (Chaotic Evil), "
    "CG (Chaotic Good), CN (Chaotic Neutral), LE (Lawful Evil), LG (Lawful Good), LN "
    "(Lawful Neutral), NE (Neutral Evil), NG (Neutral Good), N (True Neutral). "
    "Default value is 'N'.",
    type=str,
)
@click.option(
    "-background",
    default="",
    help="Character's chosen background. Available backgrounds are: Acolyte, "
    "Charlatan, Criminal, Entertainer, Folk Hero, Guild Artisan, Hermit, Noble, "
    "Outlander, Sage, Sailor, Soldier, Urchin. Default value depends on class: "
    "Barbarian (Outlander), Bard (Entertainer), Cleric (Acolyte), Druid (Hermit), "
    "Fighter (Soldier), Monk (Hermit), Paladin (Noble), Ranger (Outlander), Rogue "
    "(Charlatan), Sorcerer (Hermit), Warlock (Charlatan), and Wizard (Sage).",
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
    "subclasses are based upon the chosen class: Barbarian (Path of the "
    "Ancestral Guardian, Path of the Berserker, Path of the Storm Herald, "
    "Path of the Totem Warrior, Path of the Zealot), Bard (College of Glamour, "
    "College of Lore, College of Swords, College of Valor, College of Whispers), "
    "Cleric (Forge Domain, Grave Domain, Knowledge Domain, Life Domain, Light "
    "Domain, Nature Domain, Tempest Domain, Trickery Domain, War Domain), Druid "
    "(Circle of the Arctic, Circle of the Coast, Circle of the Desert, Circle of "
    "Dreams, Circle of the Forest, Circle of the Grassland, Circle of the Moon, "
    "Circle of the Mountain, Circle of the Shepherd, Circle of the Swamp, Circle "
    "of the Underdark), Fighter (Arcane Archer, Battle Master, Cavalier, "
    "Champion, Eldritch Knight, Samurai), Monk (Way of Shadow, Way of the Drunken "
    "Master, Way of the Four Elements, Way of the Kensei, Way of the Open Hand, "
    "Way of the Sun Soul), Paladin (Oath of the Ancients, Oath of Conquests, Oath "
    "of Devotion, Oath of Redemption, Oath of Vengeance), Ranger (Beast Master, "
    "Gloom Stalker, Horizon Walker, Hunter, Monster Slayer), Rogue (Arcane "
    "Trickster, Assassin, Inquisitive, Mastermind, Scout, Swashbuckler, Thief), "
    "Sorcerer (Divine Soul, Draconic Bloodline, Shadow Magic, Storm Sorcery, Wild "
    "Magic), Warlock (The Archfey, The Celestial, The Fiend, The Great Old One, "
    "The Hexblade), and Wizard (School of Abjuration, School of Conjuration, "
    "School of Divination, School of Enchantment, School of Evocation, School of "
    "Illusion, School of Necromancy, School of Transmutation, War Magic).",
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
@click.version_option(prog_name="yari", version=__version__)
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
    def callback(method: str, **args):
        init = eval(method)
        if all(k in args for k in ("subclass", "background", "level", "race_skills")):
            return init(
                args["subclass"], args["background"], args["level"], args["race_skills"]
            )
        elif all(
            k in args
            for k in (
                "sex",
                "subrace",
                "level",
            )
        ):
            return init(args["sex"], args["subrace"], args["level"])
        else:
            raise RuntimeError(f"Not all parameters specified for callback '{method}'.")

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = ("127.0.0.1", port)
    host, port = location
    if conn.connect_ex(location) == 0:
        out(
            f"Address {host}:{port} is already in use. Please use another port with the '-port=<DIFFERENT_PORT>' argument or close the process currently associated with this address.",
            1,
        )
    conn.close()

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

    _race = None
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
                    raise ValueError(f"'{race}' has no available subraces.")

                if subrace not in subraces_by_race:
                    raise ValueError(f"invalid subrace race '{subrace}'.")
            except ValueError as e:
                out(str(e), 1)

        _race = callback(race, sex=sex, level=level, subrace=subrace)
        _race.create()
    except (
        Exception,
        NameError,
        ValueError,
    ) as race_error:
        out(race_error, 2)

    _class = None
    try:
        if background == "":
            background = get_default_background(klass)
        else:
            if background not in ALLOWED_PC_BACKGROUNDS:
                out(f"invalid character background '{background}'.", 1)

        valid_class_subclasses = get_subclasses_by_class(klass)
        if subclass == "":
            subclass = random.choice(valid_class_subclasses)
        else:
            if subclass not in valid_class_subclasses:
                out(f"class '{klass}' has no subclass '{subclass}'.", 1)

        _class = callback(
            klass,
            background=background,
            subclass=subclass,
            level=level,
            race_skills=_race.skills,
        )
        _class.create()
    except (
        Exception,
        NameError,
        ValueError,
    ) as class_error:
        out(class_error, 2)

    try:
        # Generate ability scores.
        _attributes = AttributeGenerator(_class.primary_ability, _race.bonus, 65)
        score_array = _attributes.roll()

        # Generate character armor, tool and weapon proficiencies.
        armors = ProficiencyGenerator("armors", _class.armors, _race.armors).proficiency
        tools = ProficiencyGenerator("tools", _class.tools, _race.tools).proficiency
        weapons = ProficiencyGenerator(
            "weapons", _class.weapons, _race.weapons
        ).proficiency

        # Assign ability/feat improvements.
        _upgrade = ImprovementGenerator(
            race=race,
            subrace=subrace,
            subclass=_class.subclass,
            klass=klass,
            level=level,
            primary_ability=_class.primary_ability,
            saves=_class.saving_throws,
            magic_innate=_race.magic_innate,
            spell_slots=_class.spell_slots,
            score_array=score_array,
            languages=_race.languages,
            armor_proficiency=armors,
            tool_proficiency=tools,
            weapon_proficiency=weapons,
            skills=_class.skills,
            feats=[],
            upgrade_ratio=ratio,
        )
        _upgrade.upgrade()

        # Create proficiency data packet.
        proficiency_info = OrderedDict()
        proficiency_info["armors"] = _upgrade.armor_proficiency
        proficiency_info["tools"] = _upgrade.tool_proficiency
        proficiency_info["weapons"] = _upgrade.weapon_proficiency

        # Gather data for character sheet.
        cs = OrderedDict()
        cs["race"] = _upgrade.race
        cs["subrace"] = subrace
        cs["sex"] = sex
        cs["alignment"] = alignment
        cs["background"] = background
        cs["size"] = _race.size
        cs["height"] = _race.height
        cs["weight"] = _race.weight
        cs["class"] = klass
        cs["level"] = level
        cs["subclass"] = _upgrade.subclass
        cs["bonus"] = get_proficiency_bonus(level)
        cs["score_array"] = _upgrade.score_array
        cs["saves"] = _upgrade.saves
        cs["magic_class"] = _class.magic_class
        cs["magic_innate"] = _upgrade.magic_innate
        cs["spell_slots"] = _upgrade.spell_slots
        cs["proficiency"] = proficiency_info
        cs["languages"] = _upgrade.languages
        cs["skills"] = _upgrade.skills
        cs["feats"] = _upgrade.feats
        cs["equipment"] = _class.equipment
        cs["features"] = _class.features
        cs["traits"] = _race.traits

        try:
            with HTTPServer(cs) as http:
                http.run(port)
        except (OSError, TypeError, ValueError) as e:
            out(e, 2)
    except ValueError as error:
        out(str(error), 2)


@dataclass
class AttributeGenerator:
    """
    Assigns abilities by class, and adds racial bonuses in value/modifier pairs.

    primary_ability dict: Primary class abilities
    racial_bonus dict: Racial ability scores bonus
    threshold int: Required minimum ability score total

    """

    primary_ability: dict
    racial_bonus: dict
    threshold: int

    def _determine_ability_scores(self) -> list:
        """Generates six ability scores for assignment."""

        def _roll() -> int:
            rolls = list(roll("4d6"))
            rolls.remove(min(rolls))
            return sum(rolls)

        results = list()
        while sum(results) < self.threshold or min(results) < 8 or max(results) < 15:
            results = [_roll() for _ in range(6)]

        return results

    def roll(self) -> OrderedDict:
        """Generates character's ability scores."""
        score_array = OrderedDict()
        score_array["Strength"] = None
        score_array["Dexterity"] = None
        score_array["Constitution"] = None
        score_array["Intelligence"] = None
        score_array["Wisdom"] = None
        score_array["Charisma"] = None

        ability_choices = [
            "Strength",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
        ]

        generated_scores = self._determine_ability_scores()
        # Assign highest values to class specific abilities first.
        for ability in list(self.primary_ability.values()):
            value = max(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)

        # Assign remaining abilities/scores.
        for _ in range(0, 4):
            ability = random.choice(ability_choices)
            value = random.choice(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)

        score_array = score_array

        # Apply racial bonuses.
        for ability, bonus in self.racial_bonus.items():
            value = score_array.get(ability) + bonus
            score_array[ability] = value

        return score_array


class _AttributeBuilder:
    """
    DO NOT call class directly. Used to generate ability attributes.

    Inherited by the following classes:

        - Charisma
        - Constitution
        - Dexterity
        - Intelligence
        - Strength
        - Wisdom

    :param int score: The value of the specified ability score.
    :param list skills: The character's skill list.

    """

    def __init__(self, score: int, skills: list) -> None:
        self.attribute = self.__class__.__name__
        if self.attribute == "_Attributes":
            raise Exception(
                "This class must be inherited to use. It is currently used by "
                "the Charisma, Constitution, Dexterity, Intelligence, Strength, "
                "and Wisdom 'attribute' classes."
            )

        self.score = score
        self.attr = dict()
        self.attr["value"] = score
        self.attr["modifier"] = get_ability_modifier(self.attr.get("value"))
        self.attr["ability_checks"] = self.attr.get("modifier")
        self.attr["name"] = self.attribute
        self.attr["saving_throws"] = self.attr.get("modifier")
        self.attr["skills"] = dict()

        # Get skills associated with this attribute
        attribute_skills = [x for x in self._get_skills_by_attribute()]
        # Get the ability modifier for the associated attribute
        for skill in skills:
            if skill in attribute_skills:
                self.attr["skills"].update({skill: get_ability_modifier(score)})

    def __repr__(self):
        return '<{} score="{}">'.format(self.attribute, self.score)

    def _get_skills_by_attribute(self):
        """Returns a skill list by attribute."""
        for skill in load(file="skills"):
            attribute = load(skill, "ability", file="skills")
            if attribute == self.attribute:
                yield skill


class Charisma(_AttributeBuilder):
    def __init__(self, score: int, skills: list) -> None:
        super(Charisma, self).__init__(score, skills)


class Constitution(_AttributeBuilder):
    def __init__(self, score: int, skills: list) -> None:
        super(Constitution, self).__init__(score, skills)


class Dexterity(_AttributeBuilder):
    def __init__(self, score: int, skills: list) -> None:
        super(Dexterity, self).__init__(score, skills)


class Intelligence(_AttributeBuilder):
    def __init__(self, score: int, skills: list) -> None:
        super(Intelligence, self).__init__(score, skills)


class Strength(_AttributeBuilder):
    def __init__(self, score: int, skills: list) -> None:
        super(Strength, self).__init__(score, skills)
        self.attr["carry_capacity"] = score * 15
        self.attr["push_pull_carry"] = self.attr.get("carry_capacity") * 2
        self.attr["maximum_lift"] = self.attr.get("push_pull_carry")


class Wisdom(_AttributeBuilder):
    def __init__(self, score: int, skills: list) -> None:
        super(Wisdom, self).__init__(score, skills)


def get_ability_modifier(score: int) -> int:
    """
    Returns ability modifier by score.

    :param int score: Score to calculate modifier for.

    """
    return score != 0 and int((score - 10) / 2) or 0


class _ClassBuilder:
    """
    DO NOT call class directly. Used to generate class features.

    Inherited by the following classes:

        - Barbarian
        - Bard
        - Cleric
        - Druid
        - Fighter
        - Monk
        - Paladin
        - Ranger
        - Rogue
        - Sorcerer
        - Warlock
        - Wizard

    :param str subclass: Character's chosen subclass.
    :param str background: Character's chosen background.
    :param int level: Character's chosen level.
    :param list race_skills: Character's bonus racial skills (if applicable).

    """

    def __init__(
        self, subclass: str, background: str, level: int, race_skills: list
    ) -> None:
        self.klass = self.__class__.__name__
        if self.klass == "_Classes":
            raise Exception(
                "This class must be inherited to use. It is currently used by "
                "the Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, "
                "Ranger, Rogue, Sorcerer, Warlock and Wizard 'job' classes."
            )

        if not get_is_class(self.klass):
            raise ValueError(f"Character class '{self.klass}' is invalid.")

        if not isinstance(level, int):
            raise ValueError("Argument 'level' value must be of type 'int'.")
        elif level not in range(1, 21):
            raise ValueError("Argument 'level' value must be between 1-20.")
        else:
            self.level = level

        if self.level >= 3:
            if get_is_subclass(subclass, self.klass):
                self.subclass = subclass
            else:
                raise ValueError(
                    f"Character class '{self.klass}' has no subclass '{subclass}'."
                )
        else:
            self.subclass = ""

        if get_is_background(background):
            self.background = background
        else:
            raise ValueError(f"Character background '{background}' is invalid.")

        if not isinstance(race_skills, list):
            raise ValueError("Argument 'race_skills' value must be a 'list'.")
        else:
            self.race_skills = race_skills

        # Assign base variables
        self.all = None
        self.primary_ability = None
        self.subclasses = None
        self.default_background = None
        self.features = None
        self.hit_die = None
        self.hit_points = None
        self.proficiency_bonus = None
        self.armors = None
        self.tools = None
        self.weapons = None
        self.saving_throws = None
        self.skills = None
        self.magic_class = None
        self.spell_slots = None

    def __repr__(self):
        if self.subclass != "":
            return '<{} subclass="{}" level="{}">'.format(
                self.klass, self.subclass, self.level
            )
        else:
            return '<{} level="{}">'.format(self.klass, self.level)

    def _add_abilities(self) -> None:
        """
        Generates primary abilities by character class.

        Classes with multiple primary ability choices will select one.

            - Fighter: Strength|Dexterity
            - Fighter: Constitution|Intelligence
            - Ranger: Dexterity|Strength
            - Rogue: Charisma|Intelligence
            - Wizard: Constitution|Dexterity

        """
        class_abilities = load(self.klass, "abilities", file="classes")
        if self.klass == "Cleric":
            class_abilities[2] = random.choice(class_abilities[2])
        elif self.klass in ("Fighter", "Ranger"):
            ability_choices = class_abilities.get(1)
            class_abilities[1] = random.choice(ability_choices)
            if self.klass == "Fighter" and self.subclass != "Eldritch Knight":
                class_abilities[2] = "Constitution"
            elif self.klass == "Fighter" and self.subclass == "Eldritch Knight":
                class_abilities[2] = "Intelligence"
            else:
                class_abilities[2] = class_abilities.get(2)
        elif self.klass == "Rogue":
            if self.subclass != "Arcane Trickster":
                class_abilities[2] = "Charisma"
            else:
                class_abilities[2] = "Intelligence"
        elif self.klass == "Wizard":
            ability_choices = class_abilities.get(2)
            class_abilities[2] = random.choice(ability_choices)

        self.all["abilities"] = class_abilities

    def _add_equipment(self) -> None:
        """Generates a list of starting equipment by class & background."""
        class_equipment = load(self.klass, "equipment", file="classes")
        background_equipment = load(self.background, "equipment", file="backgrounds")
        equipment = class_equipment + background_equipment
        equipment.sort()
        self.all["equipment"] = self.equipment = equipment

    def _add_features(self) -> None:
        """Generates a dictionary of features by class, subclass & level."""

        def merge(cls_features: dict, sc_features: dict) -> dict:
            for lv, ft in sc_features.items():
                if lv in cls_features:
                    feature_list = cls_features[lv] + sc_features[lv]
                    feature_list.sort()
                    cls_features[lv] = feature_list
                else:
                    cls_features[lv] = sc_features[lv]
            return cls_features

        try:
            class_features = load(self.klass, "features", file="classes")
            if self.subclass != "":
                subclass_features = load(self.subclass, "features", file="subclasses")
                features = merge(class_features, subclass_features)
            else:
                features = class_features
            # Create feature dictionary based on level.
            features = {lv: features[lv] for lv in features if lv <= self.level}
        except (TypeError, KeyError) as e:
            # exit("Cannot find class/subclass '{}'")
            exit(e)
        else:
            for lv, fts in features.items():
                features[lv] = tuple(fts)
            self.all["features"] = features

    def _add_hit_die(self) -> None:
        """Generates hit die and point totals."""
        hit_die = self.all.get("hit_die")
        self.all["hit_die"] = f"{self.level}d{hit_die}"
        self.all["hit_points"] = hit_die
        if self.level > 1:
            new_level = self.level - 1
            die_rolls = list()
            for _ in range(0, new_level):
                hp_result = int((hit_die / 2) + 1)
                die_rolls.append(hp_result)
            self.all["hit_points"] += sum(die_rolls)

    def _add_extended_magic(self) -> None:
        """Adds extended magic spells (Domain, Warlock, etc)."""
        self.all["magic_class"] = dict()

        # If no extended magic available
        if self.subclass == "" or not has_extended_magic(self.subclass):
            return

        extended_magic_list = dict()
        # Only apply spells available at that level
        for level, spells in load(self.subclass, "magic", file="subclasses").items():
            if level <= self.level:
                extended_magic_list[level] = tuple(spells)

        self.all["magic_class"] = extended_magic_list

    def _add_proficiencies(self) -> None:
        """Merge class proficiencies with subclass proficiencies (if applicable)."""
        # If no subclass is specified
        if self.subclass == "":
            return

        # If no bonus proficiency available
        bonus_proficiency = self.all.get("proficiency")
        if bonus_proficiency is None:
            return

        for category in ("Armor", "Tools", "Weapons"):
            for index, proficiency in enumerate(bonus_proficiency):
                if category in proficiency:
                    if (
                        category
                        in (
                            "Armor",
                            "Weapons",
                        )
                        and self.subclass in ("College of Valor", "College of Swords")
                        and self.level < 3
                    ):
                        return
                    elif (
                        category == "Tools"
                        and self.subclass == "Assassin"
                        and self.level < 3
                    ):
                        return

                    try:
                        subclass_proficiency = [
                            x for x in get_subclass_proficiency(self.subclass, category)
                        ]
                        proficiencies = proficiency[1] + subclass_proficiency[0]
                        self.all["proficiency"][index] = [category, proficiencies]
                    except IndexError:
                        pass

        # Monk bonus tool or musical instrument proficiency.
        if self.klass == "Monk":
            tool_selection = [random.choice(self.all["proficiency"][1][1])]
            self.all["proficiency"][1][1] = tool_selection

        self.all["proficiency"] = [tuple(x) for x in self.all.get("proficiency")]

    def _add_skills(self):
        """Generates character's skill set."""
        # Skill handling and allotment.
        skill_pool = self.all["proficiency"][4][1]
        skills = list()

        # Get skill allotment by class.
        if self.klass in ("Rogue",):
            allotment = 4
        elif self.klass in ("Bard", "Ranger"):
            allotment = 3
        else:
            allotment = 2

        # Remove any bonus racial skill from pool.
        if len(self.race_skills) != 0:
            skill_pool = [x for x in skill_pool if x not in self.race_skills]
            skills = skills + self.race_skills

        skills = skills + random.sample(skill_pool, allotment)
        skills.sort()
        self.all["proficiency"][4] = ["Skills", skills]

        # Proficiency handling and allotment (if applicable).
        self.all["proficiency_bonus"] = get_proficiency_bonus(self.level)

    def _add_spell_slots(self):
        """Generates character's spell slots."""
        spell_slots = self.all.get("spell_slots")
        # Class has no spellcasting ability
        if spell_slots is None:
            self.all["spell_slots"] = "0"
        # Class has spellcasting ability
        else:
            # Non spellcasting Fighter/Rogue
            if self.klass in ("Fighter", "Rogue") and self.subclass not in (
                "Arcane Trickster",
                "Eldritch Knight",
            ):
                spell_slots = "0"
            else:
                spell_slots = spell_slots.get(self.level)
            self.all["spell_slots"] = spell_slots

    def create(self) -> None:
        # Load class template
        self.all = load(self.klass, file="classes")
        # Generate class fine-tuning modifications
        self._add_abilities()
        self._add_equipment()
        self._add_features()
        self._add_hit_die()
        self._add_extended_magic()
        self._add_proficiencies()
        self._add_skills()
        self._add_spell_slots()
        # Apply class fine-tuning modifications
        self.primary_ability = self.all.get("abilities")
        self.subclasses = self.all.get("subclasses")
        self.default_background = self.all.get("background")
        self.features = self.all.get("features")
        self.hit_die = self.all.get("hit_die")
        self.hit_points = self.all.get("hit_points")
        self.proficiency_bonus = self.all.get("proficiency_bonus")
        self.armors = self.all.get("proficiency")[0][1]
        self.tools = self.all.get("proficiency")[1][1]
        self.weapons = self.all.get("proficiency")[2][1]
        self.saving_throws = self.all.get("proficiency")[3][1]
        self.skills = self.all.get("proficiency")[4][1]
        self.magic_class = self.all["magic_class"]
        self.spell_slots = self.all.get("spell_slots")
        # Delete class template
        del self.all


class Barbarian(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Barbarian, self).__init__(subclass, background, level, race_skills)


class Bard(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Bard, self).__init__(subclass, background, level, race_skills)


class Cleric(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Cleric, self).__init__(subclass, background, level, race_skills)


class Druid(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Druid, self).__init__(subclass, background, level, race_skills)


class Fighter(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Fighter, self).__init__(subclass, background, level, race_skills)


class Monk(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Monk, self).__init__(subclass, background, level, race_skills)


class Paladin(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Paladin, self).__init__(subclass, background, level, race_skills)


class Ranger(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Ranger, self).__init__(subclass, background, level, race_skills)


class Rogue(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Rogue, self).__init__(subclass, background, level, race_skills)


class Sorcerer(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Sorcerer, self).__init__(subclass, background, level, race_skills)


class Warlock(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Warlock, self).__init__(subclass, background, level, race_skills)


class Wizard(_ClassBuilder):
    def __init__(self, subclass, background, level, race_skills) -> None:
        super(Wizard, self).__init__(subclass, background, level, race_skills)


def get_default_background(klass: str):
    """
    Returns the default background by klass.

    :param str klass: Characters chosen class.

    """
    return load(klass, "background", file="classes")


def get_is_background(background: str) -> bool:
    """
    Returns whether the background is valid.

    :param str background: Chosen background to check.

    """
    return background in load(file="backgrounds")


def get_is_class(klass: str) -> bool:
    """
    Returns whether the klass is valid.

    :param str klass: Character's chosen class.

    """
    return klass in load(file="classes")


def get_is_subclass(subclass: str, klass: str) -> bool:
    """
    Returns whether subclass is a valid subclass of klass.

    :param str subclass: Character's chosen subclass.
    :param str klass: Character's chosen class.

    """
    return subclass in load(klass, "subclasses", file="classes")


def get_subclass_proficiency(subclass: str, category: str):
    """
    Returns subclass bonus proficiencies (if ANY).

    :param str subclass: Character subclass to get proficiencies for.
    :param str category: Proficiency category to get proficiencies for.

    """
    if category not in ("Armor", "Tools", "Weapons"):
        raise ValueError("Argument 'category' must be 'Armor', 'Tools' or 'Weapons'.")

    trait_list = load(subclass, file="subclasses")
    if trait_list.get("proficiency") is not None:
        proficiencies = trait_list.get("proficiency")
        for proficiency in proficiencies:
            if proficiency[0] == category:
                yield proficiency[1]


def get_all_languages() -> list:
    return load(file="languages")


def get_all_skills() -> list:
    """Returns a list of ALL skills."""
    return load(file="skills")


def get_background_skills(background: str):
    """
    Returns bonus skills by background (if applicable).

    :param str background: Background to return background skills for.

    """
    return load(background, "skills", file="backgrounds")


def get_subclasses_by_class(klass: str) -> tuple:
    """
    Returns a tuple of valid subclasses for klass.

    :param str klass: Character's class.

    """
    return load(klass, "subclasses", file="classes")


def get_proficiency_bonus(level: int) -> int:
    """
    Returns a proficiency bonus value by level.

    :param int level: Level of character.

    """
    return math.ceil((level / 4) + 1)


def has_extended_magic(subclass: str) -> bool:
    """
    Returns whether class subclass has spells.

    :param str subclass: Character's subclass.

    """
    extra_magic = load(subclass, "magic", file="subclasses")
    if extra_magic is not None:
        return True
    return False


@dataclass
class ImprovementGenerator:
    """
    Applies level based upgrades.

    race str: Character's race
    subrace str: Character's subrace (if applicable)
    klass str: Character's class
    subclass str: Character's subclass
    level int: Character's level
    primary_ability dict: Character's primary class abilities
    saves list: Character's saving throws
    magic_innate list: Character's innate magic (if applicable)
    spell_slots str: Character's spell slots
    score_array OrderedDict: Character's ability scores
    languages list: Character's languages
    armor_proficiency list: Character's armor proficiencies
    tool_proficiency list: Character's tool proficiencies
    weapon_proficiency list: Character's weapon proficiencies
    skills list: Character's skills
    feats list: Character's feats
    upgrade_ratio int: Character's ability/feat upgrade ratio

    """

    race: str
    subrace: str
    klass: str
    subclass: str
    level: int
    primary_ability: dict
    saves: list
    magic_innate: list
    spell_slots: str
    score_array: OrderedDict
    languages: list
    armor_proficiency: list
    tool_proficiency: list
    weapon_proficiency: list
    skills: list
    feats: list
    upgrade_ratio: int

    def _add_bonus_proficiency(self):
        """Adds special bonus class proficiencies (if applicable)."""
        if self.klass == "Druid":
            self.languages.append("Druidic")
        elif self.klass == "Rogue":
            self.languages.append("Thieves' cant")

        if self.level >= 3:
            if self.subclass == "Cavalier":
                cavalier_skills = [
                    "Animal Handling",
                    "History",
                    "Insight",
                    "Performance",
                    "Persuasion",
                ]
                cavalier_skills = [s for s in cavalier_skills if s not in self.skills]
                self.skills = self.skills + random.sample(cavalier_skills, 1)
            elif self.subclass == "College of Lore":
                lore_skills = [x for x in get_all_skills() if x not in self.skills]
                self.skills = self.skills + random.sample(lore_skills, 3)
            elif self.subclass == "Samurai":
                proficiency_choice = random.choice(("Language", "Skill"))
                if proficiency_choice == "Language":
                    samurai_language = [
                        x for x in get_all_languages() if x not in self.languages
                    ]
                    self.languages = self.languages + random.sample(samurai_language, 1)
                elif proficiency_choice == "Skill":
                    samurai_skills = [
                        "History",
                        "Insight",
                        "Performance",
                        "Persuasion",
                    ]
                    samurai_skills = [s for s in samurai_skills if s not in self.skills]
                    self.skills = self.skills + random.sample(samurai_skills, 1)
            elif self.subclass == "Way of the Drunken Master":
                self.skills.append("Performance")

    def _add_feat(self) -> None:
        """Randomly selects and adds a valid feats."""
        feats = [feat for feat in list(load(file="feats")) if feat not in self.feats]
        random.shuffle(feats)
        feat_choice = feats.pop()
        out(f"Checking prerequisites for '{feat_choice}'...", -2)
        # Keep choosing a feat until prerequisites met.
        if not self._has_prerequisites(feat_choice):
            out(f"Prerequisites not met for '{feat_choice}'.", -1)
            while not self._has_prerequisites(feat_choice):
                random.shuffle(feats)
                feat_choice = feats.pop()
                out(f"Checking prerequisites for '{feat_choice}'...", -2)
                if not self._has_prerequisites(feat_choice):
                    out(f"Prerequisites not met for '{feat_choice}'.", -1)
        # Prerequisites met, inform, add to list and apply features.
        out(f"Prerequisites met for '{feat_choice}'.")
        self._add_features(feat_choice)
        self.feats.append(feat_choice)

    def _add_features(self, feat: str) -> None:
        """
        Assign associated features by specified feat.

        :param str feat: Feat to add features for.

        """
        # Actor
        if feat == "Actor":
            self._set_feat_ability(["Charisma"])

        # Athlete/Lightly Armored/Moderately Armored/Weapon Master
        if feat in (
            "Athlete",
            "Lightly Armored",
            "Moderately Armored",
            "Weapon Master",
        ):
            self._set_feat_ability(["Strength", "Dexterity"])
            if feat == "Lightly Armored":
                self.armor_proficiency.append("Light")
            elif feat == "Moderately Armored":
                self.armor_proficiency.append("Medium")
                self.armor_proficiency.append("Shield")

        # Dragon Fear/Dragon Hide
        if feat in ("Dragon Fear", "Dragon Hide"):
            self._set_feat_ability(["Strength", "Constitution", "Charisma"])

        # Drow High Magic/Svirfneblin Magic/Wood Elf Magic
        if feat in ("Drow High Magic", "Svirfneblin Magic", "Wood Elf Magic"):
            if feat == "Drow High Magic":
                self.magic_innate.append("Detect Magic")
                self.magic_innate.append("Dispel Magic")
                self.magic_innate.append("Levitate")
            elif feat == "Svirfneblin Magic":
                self.magic_innate.append("Blindness/Deafness")
                self.magic_innate.append("Blur")
                self.magic_innate.append("Disguise")
                self.magic_innate.append("Nondetection")
            elif feat == "Wood Elf Magic":
                druid_cantrips = (
                    "Druidcraft",
                    "Guidance",
                    "Mending",
                    "Poison Spray",
                    "Produce Flame",
                    "Resistance",
                    "Shillelagh",
                    "Thorn Whip",
                )
                self.magic_innate.append(random.choice(druid_cantrips))
                self.magic_innate.append("Longstrider")
                self.magic_innate.append("Pass Without Trace")

        # Durable/Dwarven Fortitude
        if feat in ("Durable", "Dwarven Fortitude", "Infernal Constitution"):
            self._set_feat_ability(
                [
                    "Constitution",
                ]
            )

        # Elven Accuracy
        if feat == "Elven Accuracy":
            self._set_feat_ability(
                [
                    "Dexterity",
                    "Intelligence",
                    "Wisdom",
                    "Charisma",
                ]
            )

        # Fey Teleportation
        if feat == "Fey Teleportation":
            self._set_feat_ability(
                [
                    "Intelligence",
                    "Charisma",
                ]
            )

        # Flames of Phlegethos
        if feat == "Flames of Phlegethos":
            self._set_feat_ability(["Intelligence", "Charisma"])

        # Heavily Armored/Heavy Armor Master
        if feat in ("Heavily Armored", "Heavy Armor Master"):
            self._set_feat_ability(
                [
                    "Strength",
                ]
            )
            if feat == "Heavily Armored":
                self.armor_proficiency.append("Heavy")

        # Keen Mind/Linguist/Prodigy
        if feat in ("Fade Away", "Keen Mind", "Linguist", "Prodigy"):
            if feat in ("Fade Away", "Prodigy"):
                self._set_feat_ability(
                    [
                        "Intelligence",
                    ]
                )
            if feat in ("Linguist", "Prodigy"):
                # Remove already known languages.
                linguist_languages = list(load(file="languages"))
                linguist_languages = [
                    language
                    for language in linguist_languages
                    if language not in self.languages
                ]

                if feat == "Linguist":
                    self.languages = self.languages + random.sample(
                        linguist_languages, 3
                    )
                else:
                    self.languages = self.languages + random.sample(
                        linguist_languages, 1
                    )

        # Observant
        if feat == "Observant":
            if self.klass in ("Cleric", "Druid"):
                self._set_feat_ability(
                    [
                        "Wisdom",
                    ]
                )
            elif self.klass in ("Wizard",):
                self._set_feat_ability(
                    [
                        "Intelligence",
                    ]
                )

        # Orcish Fury
        if feat == "Orcish Fury":
            self._set_feat_ability(
                [
                    "Strength",
                    "Constitution",
                ]
            )

        # Prodigy/Skilled
        if feat in ("Prodigy", "Skilled"):
            if feat == "Prodigy":
                skills = [
                    skill
                    for skill in list(load(file="skills"))
                    if skill not in self.skills
                ]
                tool_list = [t for t in get_tool_chest()]
                tool_list = [
                    tool for tool in tool_list if tool not in self.tool_proficiency
                ]
                self.skills.append(random.choice(skills))
                self.tool_proficiency.append(random.choice(tool_list))
            else:
                for _ in range(3):
                    skills = [
                        skill
                        for skill in list(load(file="skills"))
                        if skill not in self.skills
                    ]
                    tool_list = [t for t in get_tool_chest()]
                    tool_list = [
                        tool for tool in tool_list if tool not in self.tool_proficiency
                    ]
                    skilled_choice = random.choice(["Skill", "Tool"])
                    # Bonus skill added
                    if skilled_choice == "Skill":
                        skill_choice = random.choice(skills)
                        self.skills.append(skill_choice)
                        out(f"Feat '{feat}' added skill '{skill_choice}'.", -2)
                    # Bonus tool proficiency added
                    elif skilled_choice == "Tool":
                        tool_choice = random.choice(tool_list)
                        self.tool_proficiency.append(tool_choice)
                        out(
                            f"Feat '{feat}' added tool proficiency '{tool_choice}'.", -2
                        )

        # Resilient
        if feat == "Resilient":
            # Remove all proficient saving throws.
            resilient_saves = [
                "Strength",
                "Dexterity",
                "Constitution",
                "Intelligence",
                "Wisdom",
                "Charisma",
            ]
            resilient_saves = [
                save for save in resilient_saves if save not in self.saves
            ]
            # Choose one non-proficient saving throw.
            ability_choice = random.sample(resilient_saves, 1)
            self._set_feat_ability(ability_choice)
            self.saves = self.saves + ability_choice

        # Second Chance
        if feat == "Second Chance":
            self._set_feat_ability(
                [
                    "Dexterity",
                    "Constitution",
                    "Charisma",
                ]
            )

        # Squat Nimbleness
        if feat == "Squat Nimbleness":
            self._set_feat_ability(["Dexterity", "Strength"])
            if "Acrobatics" and "Athletics" in self.skills:
                pass
            else:
                skill_choice = random.choice(("Acrobatics", "Athletics"))
                if "Acrobatics" in self.skills:
                    skill_choice = "Athletics"
                elif "Athletics" in self.skills:
                    skill_choice = "Acrobatics"
                self.skills.append(skill_choice)
                out(f"Feat '{feat}' added skill '{skill_choice}'.", -2)

        # Tavern Brawler
        if feat == "Tavern Brawler":
            self._set_feat_ability(["Strength", "Constitution"])
            self.weapon_proficiency.append("Improvised weapons")
            self.weapon_proficiency.append("Unarmed strikes")

        # Weapon Master
        if feat == "Weapon Master":
            weapons = [t for t in get_weapon_chest()]
            selections = weapons[0]
            # Has Simple weapon proficiency.
            if "Simple" in self.weapon_proficiency:
                # Has Simple proficiency and tight list of weapon proficiencies.
                del selections["Simple"]
                selections = selections.get("Martial")
                if len(self.weapon_proficiency) > 1:
                    tight_weapon_list = [
                        proficiency
                        for proficiency in self.weapon_proficiency
                        if proficiency != "Simple"
                    ]
                    selections = [
                        selection
                        for selection in selections
                        if selection not in tight_weapon_list
                    ]
                    tight_weapon_list.clear()
            # Doesn't have Simple or Martial proficiency but a tight list of weapons.
            elif "Simple" and "Martial" not in self.weapon_proficiency:
                selections = selections.get("Martial") + selections.get("Simple")
                selections = [
                    selection
                    for selection in selections
                    if selection not in self.weapon_proficiency
                ]

            self.weapon_proficiency = self.weapon_proficiency + random.sample(
                selections, 4
            )
            selections.clear()

    def _get_upgrade_ratio(self, percentage: int) -> tuple:
        """Returns an 'ability to feat' upgrade ration by percentage."""
        if percentage not in range(0, 101):
            raise ValueError("Argument 'percentage' value must be between 0-100.")
        elif (percentage % 10) != 0:
            raise ValueError("Argument 'percentage' value must be a multiple of 10.")
        else:
            num_of_upgrades = 0
            for _ in range(1, self.level + 1):
                if (_ % 4) == 0 and _ != 20:
                    num_of_upgrades += 1

            if self.klass == "Fighter" and self.level >= 6:
                num_of_upgrades += 1

            if self.klass == "Rogue" and self.level >= 8:
                num_of_upgrades += 1

            if self.klass == "Fighter" and self.level >= 14:
                num_of_upgrades += 1

            if self.level >= 19:
                num_of_upgrades += 1

            percentage = float(percentage)
            ability_upgrades = math.floor(num_of_upgrades * percentage / 100.0)
            feat_upgrades = num_of_upgrades - ability_upgrades
            return ability_upgrades, feat_upgrades

    def _has_prerequisites(self, feat: str) -> bool:
        """
        Determines if character has the prerequisites for feat.

        :param str feat: Feat to check prerequisites for.

        """
        if feat in self.feats:
            return False

        # If Heavily, Lightly, or Moderately Armored feat and a Monk.
        if (
            feat
            in (
                "Heavily Armored",
                "Lightly Armored",
                "Moderately Armored",
            )
            and self.klass == "Monk"
        ):
            return False
        # Chosen feat is "Armored" or Weapon Master but already proficient w/ assoc. armor type.
        elif feat in (
            "Heavily Armored",
            "Lightly Armored",
            "Moderately Armored",
            "Weapon Master",
        ):
            # Character already has heavy armor proficiency.
            if feat == "Heavily Armored" and "Heavy" in self.armor_proficiency:
                return False
            # Character already has light armor proficiency.
            elif feat == "Lightly Armored" and "Light" in self.armor_proficiency:
                return False
            # Character already has medium armor proficiency.
            elif feat == "Moderately Armored" and "Medium" in self.armor_proficiency:
                return False
            # Character already has martial weapon proficiency.
            elif feat == "Weapon Master" and "Martial" in self.weapon_proficiency:
                return False

        # Go through ALL additional prerequisites.
        prerequisite = load(feat, file="feats")
        for requirement, _ in prerequisite.items():
            if requirement == "abilities":
                for ability, required_score in prerequisite.get(requirement).items():
                    my_score = self.score_array[ability]
                    if my_score < required_score:
                        return False

            if requirement == "caster":
                # Basic spell caster check, does the character have spells?
                if self.spell_slots == "0":
                    return False

                # Magic Initiative
                if feat == "Magic Initiative" and self.klass not in (
                    "Bard",
                    "Cleric",
                    "Druid",
                    "Sorcerer",
                    "Warlock",
                    "Wizard",
                ):
                    return False

                # Ritual Caster
                if feat == "Ritual Caster":
                    my_score = 0
                    required_score = 0
                    if self.klass in ("Cleric", "Druid"):
                        my_score = self.score_array.get("Wisdom")
                        required_score = prerequisite.get("abilities").get("Wisdom")
                    elif self.klass == "Wizard":
                        my_score = self.score_array.get("Intelligence")
                        required_score = prerequisite.get("abilities").get(
                            "Intelligence"
                        )

                    if my_score < required_score:
                        return False

            if requirement == "proficiency":
                if feat in (
                    "Heavy Armor Master",
                    "Heavily Armored",
                    "Medium Armor Master",
                    "Moderately Armored",
                ):
                    armors = prerequisite.get(requirement).get("armors")
                    for armor in armors:
                        if armor not in self.armor_proficiency:
                            return False

            if requirement == "race":
                if self.race not in prerequisite.get(requirement):
                    return False

            if requirement == "subrace":
                if self.subrace not in prerequisite.get(requirement):
                    return False
        return True

    def _is_adjustable(self, abilities: (list, str), bonus: int = 1) -> bool:
        """
        Determines if an ability can be adjusted i.e: not over 20.

        :param list abilities: Ability score(s) to be checked.

        """
        try:
            if isinstance(abilities, list):
                for ability in abilities:
                    if (self.score_array[ability] + bonus) > 20:
                        raise ValueError
            elif isinstance(abilities, str):
                if (self.score_array[abilities] + bonus) > 20:
                    raise ValueError
            else:
                raise RuntimeError
        except RuntimeError:
            traceback.print_exc()
        except ValueError:
            return False
        else:
            return True

    def _set_ability_score(self, ability_array: list) -> None:
        """
        Adjust a specified ability_array score with bonus.

        :param list ability_array: ability_array score to set.

        """
        try:
            # Ensure score_array object is type OrderedDict
            if not isinstance(self.score_array, OrderedDict):
                raise TypeError("Object 'score_array' is not type 'OrderedDict'.")

            if len(ability_array) == 1:
                bonus = 2
            elif len(ability_array) == 2:
                bonus = 1
            else:
                raise RuntimeError("Argument 'ability_array' require 1 or 2 values.")

            for ability in ability_array:
                if ability not in self.score_array:
                    raise KeyError(f"Argument 'ability_array' is invalid. ({ability}).")
                elif not self._is_adjustable(ability, bonus):
                    raise ValueError(
                        f"Argument 'ability_array' is not upgradeable ({ability})."
                    )
                else:
                    value = self.score_array.get(ability) + bonus
                    self.score_array[ability] = value
        except (KeyError, TypeError):
            traceback.print_exc()
        except RuntimeError as err:
            exit(err)
        except ValueError:
            pass

    def _set_feat_ability(self, ability_options: list) -> None:
        """
        Adjust a specified ability_array score with bonus.

        :param list ability_options: ability_array score to set.

        """

        def set_ability(score_array: OrderedDict, ability_choice):
            value = score_array.get(ability_choice) + 1
            score_array[ability_choice] = value

        try:
            # Ensure score_array object is type OrderedDict
            if not isinstance(self.score_array, OrderedDict):
                raise TypeError("Object 'score_array' is not type 'OrderedDict'.")

            # If only one ability option available
            if len(ability_options) == 1:
                set_ability(self.score_array, ability_options[0])
                return

            is_upgraded = False
            primary_ability = list(self.primary_ability.values())

            # Choose primary ability over other options (if applicable)
            for ability in primary_ability:
                if ability in ability_options:
                    if self._is_adjustable(ability):
                        set_ability(self.score_array, ability)
                        is_upgraded = True
                        break
                    else:
                        ability_options.remove(ability)

            # Choose any one ability option if not upgraded above
            if not is_upgraded:
                ability = random.choice(ability_options)
                set_ability(self.score_array, ability)
        except (KeyError, TypeError):
            traceback.print_exc()

    def upgrade(self):
        """Runs character upgrades (if applicable)."""
        self._add_bonus_proficiency()

        # Determine and assign upgrades by ability/feat upgrade ratio.
        upgrade_ratio = self._get_upgrade_ratio(self.upgrade_ratio)
        if sum(upgrade_ratio) == 0:
            return

        ability_upgrades = upgrade_ratio[0]
        feat_upgrades = upgrade_ratio[1]

        # Handle ability score upgrades
        if ability_upgrades > 0:
            primary_ability = list(self.primary_ability.values())
            for _ in range(0, ability_upgrades):
                try:
                    if not self._is_adjustable(primary_ability):
                        raise ValueError("No upgradeable primary abilities.")

                    bonus_type = random.choice([1, 2])
                    # +1 bonus two abilities
                    if bonus_type == 1 and self._is_adjustable(primary_ability):
                        self._set_ability_score(primary_ability)
                    # +2 bonus one ability - 1st ability upgradeable
                    elif bonus_type == 2 and self._is_adjustable(primary_ability[0]):
                        self._set_ability_score([primary_ability[0]])
                    # +2 bonus one ability - 1st ability not upgradeable, choose 2nd
                    elif bonus_type == 2 and self._is_adjustable(primary_ability[1]):
                        self._set_ability_score([primary_ability[1]])
                    # Neither ability upgradable
                    else:
                        raise ValueError("No upgradeable primary ability by bonus.")
                except ValueError:
                    self._add_feat()

            # Handle feat upgrades
            if feat_upgrades > 0:
                for _ in range(0, feat_upgrades):
                    self._add_feat()


class ProficiencyGenerator:
    """
    Merges class with racial proficiencies (if applicable).

    :param str proficiency_type: Proficiency type (armors|tools|weapons).
    :param list class_proficiency: Class based proficiency by proficiency_type.
    :param list race_proficiency: Race based proficiency by proficiency_type (if applicable).

    """

    def __init__(
        self, proficiency_type: str, class_proficiency: list, race_proficiency: list
    ) -> None:
        if proficiency_type not in ("armors", "tools", "weapons"):
            raise ValueError(
                f"Invalid 'proficiency_type' argument '{proficiency_type}' specified."
            )

        race_proficiency = [p for p in race_proficiency if p not in class_proficiency]
        if len(race_proficiency) != 0:
            self.proficiency = class_proficiency + race_proficiency
        else:
            self.proficiency = class_proficiency


def get_armor_chest():
    """Returns a full collection of armors."""
    armor_chest = dict()
    for armor_category in ("Heavy", "Light", "Medium"):
        armor_chest[armor_category] = load(armor_category, file="armors")
    yield armor_chest


def get_tool_chest():
    """Returns a full collection of tools."""
    for main_tool in load(file="tools"):
        if main_tool in ("Artisan's tools", "Gaming set", "Musical instrument"):
            for sub_tool in load(main_tool, file="tools"):
                yield f"{main_tool} - {sub_tool}"
        else:
            yield main_tool


def get_weapon_chest():
    """Returns a full collection of weapons."""
    weapon_chest = dict()
    for weapon_category in ("Simple", "Martial"):
        weapon_chest[weapon_category] = load(weapon_category, file="weapons")
    yield weapon_chest


class _RaceBuilder:
    """
    DO NOT call class directly. Used to generate racial traits.

    Inherited by the following classes:

        - Aasimar
        - Bugbear
        - Dragonborn
        - Dwarf
        - Elf
        - Firbolg
        - Gith
        - Gnome
        - Goblin
        - Goliath
        - HalfElf
        - HalfOrc
        - Halfling
        - Hobgoblin
        - Human
        - Kenku
        - Kobold
        - Lizardfolk
        - Orc
        - Tabaxi
        - Tiefling
        - Triton
        - Yuan-ti

    :param str sex: Character's chosen gender.
    :param str subrace: Character's chosen subrace (if applicable).
    :param int level: Character's chosen level.

    """

    def __init__(self, sex: str, subrace: str = "", level: int = 1) -> None:
        self.race = self.__class__.__name__
        valid_subraces = [
            sr for sr in get_subraces_by_race(ALLOWED_PC_SUBRACES, self.race)
        ]

        if self.race == "_Races":
            raise Exception(
                "This class must be inherited to use. It is currently used by "
                "the Aasimar, Bugbear, Dragonborn, Dwarf, Elf, Firbolg, Gith, "
                "Gnome, Goblin, Goliath, HalfElf, HalfOrc, Halfling, Hobgoblin, "
                "Human, Kenku, Kobold, Lizardfolk, Orc, Tabaxi, Tiefling, "
                "Triton, and Yuanti 'race' classes."
            )

        if sex in (
            "Female",
            "Male",
        ):
            self.sex = sex
        else:
            raise ValueError(f"Argument 'sex' value must be 'Male' or 'Female'.")

        if not has_subraces(self.race):
            self.subrace = ""
        else:
            if subrace not in valid_subraces:
                raise ValueError(
                    f"Argument 'subrace' value '{subrace}' is invalid for '{self.race}'."
                )
            elif len(valid_subraces) != 0 and subrace == "":
                raise ValueError(f"Argument 'subrace' is required for '{self.race}'.")
            else:
                self.subrace = subrace

        if not isinstance(level, int):
            raise ValueError("Argument 'level' value must be of type 'int'.")
        else:
            self.level = level

    def __repr__(self):
        if self.subrace != "":
            return '<{} subrace="{}" sex="{}" level="{}">'.format(
                self.race, self.subrace, self.sex, self.level
            )
        else:
            return '<{} sex="{}" level="{}">'.format(self.race, self.sex, self.level)

    def _add_ability_bonus(self):
        """Adds Half-Elves chosen bonus racial ability bonus (if applicable)."""
        if self.race == "HalfElf":
            valid_abilities = [
                "Strength",
                "Dexterity",
                "Constitution",
                "Intelligence",
                "Wisdom",
            ]
            valid_abilities = random.sample(valid_abilities, 2)
            for ability in valid_abilities:
                self.all["bonus"][ability] = 1

    def _add_mass(self) -> None:
        """Generates and sets character's height & weight."""
        height_base = self.all.get("ratio").get("height").get("base")
        height_modifier = self.all.get("ratio").get("height").get("modifier")
        height_modifier = sum(list(roll(height_modifier)))
        self.height = height_base + height_modifier

        weight_base = self.all.get("ratio").get("weight").get("base")
        weight_modifier = self.all.get("ratio").get("weight").get("modifier")
        weight_modifier = sum(list(roll(weight_modifier)))
        self.weight = (height_modifier * weight_modifier) + weight_base

    def _add_traits(self):
        """
        Add all bonus armor, tool, and/or weapon proficiencies, and other traits.

        """
        # Set default attribute values
        self.all = load(self.race, file="races")
        self.ancestor = (
            self.race == "Dragonborn"
            and random.choice(
                (
                    "Black",
                    "Blue",
                    "Brass",
                    "Bronze",
                    "Copper",
                    "Gold",
                    "Green",
                    "Red",
                    "Silver",
                    "White",
                )
            )
            or None
        )
        self.bonus = self.all.get("bonus")
        self.darkvision = 0
        self.languages = self.all.get("languages")
        self.magic_innate = list()
        self.ratio = self.all.get("ratio")
        self.size = self.all.get("size")
        self.traits = list()
        self.resistances = list()

        self.skills = list()
        self.armors = list()
        self.tools = list()
        self.weapons = list()

        for trait in self.all.get("traits"):
            if len(trait) == 1:
                if trait[0] not in ("Breath Weapon", "Damage Resistance", "Draconic Ancestry"):
                    self.traits.append(trait[0])
                else:
                    if trait[0] in ("Breath Weapon", "Damage Resistance"):
                        if self.ancestor in (
                            "Black",
                            "Copper",
                        ):
                            self.resistances.append("Acid")
                        elif self.ancestor in (
                            "Blue",
                            "Bronze",
                        ):
                            self.resistances.append("Lightning")
                        elif self.ancestor in (
                            "Brass",
                            "Gold",
                            "Red",
                        ):
                            self.resistances.append("Fire")
                        elif self.ancestor == "Green":
                            self.resistances.append("Poison")
                        elif self.ancestor in ("Silver", "White"):
                            self.resistances.append("Cold")
                        self.traits.append(f"{trait[0]} ({self.resistances[-1]})")
                    else:
                        self.traits.append(f"{trait[0]} ({self.ancestor})")
            else:
                (name, value) = trait
                self.traits.append(name)
                if name == "Darkvision":
                    if self.darkvision == 0:
                        self.darkvision = value
                elif name == "Superior Darkvision":
                    if value > self.darkvision:
                        self.darkvision = value
                elif name == "Cantrip":
                    self.magic_innate = random.sample(value, 1)
                elif name == "Natural Illusionist":
                    self.magic_innate = [value]
                elif name in (
                    "Drow Magic",
                    "Duergar Magic",
                    "Githyanki Psionics",
                    "Githzerai Psionics",
                    "Infernal Legacy",
                    "Innate Spellcasting",
                    "Legacy of Avernus",
                    "Legacy of Cania",
                    "Legacy of Dis",
                    "Legacy of Maladomini",
                    "Legacy of Malbolge",
                    "Legacy of Minauros",
                    "Legacy of Phlegethos",
                    "Legacy of Stygia",
                ):
                    self.magic_innate = [spell[1] for spell in value]
                elif (
                    name in ("Necrotic Shroud", "Radiant Consumption", "Radiant Soul")
                    and self.level >= 3
                ):
                    self.traits.append(name)
                elif name in (
                    "Celestial Resistance",
                    "Duergar Resilience",
                    "Dwarven Resilience",
                    "Fey Ancestry",
                    "Stout Resilience",
                ):
                    self.resistances = self.resistances + value
                elif name in (
                    "Cat's Talent",
                    "Keen Senses",
                    "Menacing",
                    "Natural Athlete",
                    "Sneaky",
                ):
                    self.skills.append(value[0])
                elif name in ("Decadent Mastery", "Extra Language", "Languages"):
                    self.languages.append(random.choice(value))
                elif name in ("Hunter's Lore", "Kenku Training", "Skill Versatility"):
                    self.skills = self.skills + random.sample(value, 2)
                elif name in (
                    "Dwarven Armor Training",
                    "Martial Prodigy (Armor)",
                    "Martial Training (Armor)",
                ):
                    self.armors = value
                elif name == "Tinker":
                    self.tools.append(value)
                elif name == "Tool Proficiency":
                    self.tools.append(random.choice(value))
                elif name in (
                    "Drow Weapon Training",
                    "Dwarven Combat Training",
                    "Elf Weapon Training",
                    "Martial Prodigy (Weapon)",
                    "Sea Elf Training",
                ):
                    self.weapons = value
                elif name in "Martial Training (Weapon)":
                    self.weapons = random.sample(value, 2)

    def _add_subrace_traits(self) -> None:
        """ Merges subrace traits with race traits. """
        # Ignore if no subrace specified
        if self.subrace == "":
            return

        # Load subrace traits
        subrace_traits = load(self.subrace, file="subraces")
        # Attempt to merge traits
        for trait, value in subrace_traits.items():
            if trait not in self.all:
                self.all[trait] = subrace_traits[trait]
            elif trait == "bonus":
                for ability, bonus in value.items():
                    self.all[trait][ability] = bonus
            elif trait == "ratio":
                ratio = subrace_traits.get(trait)
                if ratio is not None:
                    self.all[trait] = ratio
            elif trait == "traits":
                for other in subrace_traits.get(trait):
                    self.all[trait].append(other)
        # Updates attributes w/ merged trait values
        self.bonus = self.all.get("bonus")
        self.languages = self.all.get("languages")

    def create(self) -> None:
        """Generates the character's basic racial attributes."""
        self._add_traits()
        self._add_subrace_traits()
        self._add_ability_bonus()
        self._add_mass()
        del self.all


class Aasimar(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Aasimar, self).__init__(sex, subrace, level)


class Bugbear(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Bugbear, self).__init__(sex, subrace, level)


class Dragonborn(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Dragonborn, self).__init__(sex, subrace, level)


class Dwarf(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Dwarf, self).__init__(sex, subrace, level)


class Elf(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Elf, self).__init__(sex, subrace, level)


class Firbolg(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Firbolg, self).__init__(sex, subrace, level)


class Gith(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Gith, self).__init__(sex, subrace, level)


class Gnome(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Gnome, self).__init__(sex, subrace, level)


class Goblin(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Goblin, self).__init__(sex, subrace, level)


class Goliath(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Goliath, self).__init__(sex, subrace, level)


class HalfElf(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(HalfElf, self).__init__(sex, subrace, level)


class HalfOrc(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(HalfOrc, self).__init__(sex, subrace, level)


class Halfling(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Halfling, self).__init__(sex, subrace, level)


class Hobgoblin(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Hobgoblin, self).__init__(sex, subrace, level)


class Human(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Human, self).__init__(sex, subrace, level)


class Kenku(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Kenku, self).__init__(sex, subrace, level)


class Kobold(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Kobold, self).__init__(sex, subrace, level)


class Lizardfolk(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Lizardfolk, self).__init__(sex, subrace, level)


class Orc(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Orc, self).__init__(sex, subrace, level)


class Tabaxi(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Tabaxi, self).__init__(sex, subrace, level)


class Tiefling(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Tiefling, self).__init__(sex, subrace, level)


class Triton(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Triton, self).__init__(sex, subrace, level)


class Yuanti(_RaceBuilder):
    def __init__(self, sex, subrace, level) -> None:
        super(Yuanti, self).__init__(sex, subrace, level)


def get_subraces_by_race(allowed_subraces: list, race: str):
    """Yields a list of valid subraces by race.

    :param list allowed_subraces: List of allowed subraces.
    :param str race: Race to retrieve subraces for.

    """
    for subrace in allowed_subraces:
        if load(subrace, "parent", file="subraces") == race:
            yield subrace


def has_subraces(race: str) -> bool:
    """
    Determines if race has subraces.

    :param str race: Race to determine if it has subraces.

    """
    try:
        subraces = [s for s in get_subraces_by_race(ALLOWED_PC_SUBRACES, race)][0]
    except IndexError:
        return False
    else:
        return subraces


class HTTPServer:
    """
    Creates the HTTPServer object.

    :param OrderedDict data: Character's information packet.

    """

    def __init__(self, data: OrderedDict) -> None:
        if not isinstance(data, OrderedDict):
            raise TypeError("Argument 'data' must be of type 'OrderedDict'.")

        data_keys = (
            "race",
            "subrace",
            "sex",
            "alignment",
            "background",
            "size",
            "height",
            "weight",
            "class",
            "subclass",
            "level",
            "bonus",
            "score_array",
            "saves",
            "proficiency",
            "languages",
            "magic_innate",
            "spell_slots",
            "skills",
            "feats",
            "equipment",
            "features",
            "traits",
        )
        if not all(dk in data for dk in data_keys):
            raise ValueError(
                "All data keys 'race', 'subrace', 'sex', 'alignment', "
                "'background', 'size', 'height', 'weight', 'class', 'subclass', "
                "'level', 'bonus', 'score_array', 'saves', 'proficiency', "
                "'languages', 'magic_innate', 'spell_slots', 'skills', 'feats', "
                "'equipment', 'features', 'traits' must have a value."
            )
        else:
            self.data = data
        self.text = ""

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

    @property
    def body(self):
        return self.text

    @body.setter
    def body(self, text: str):
        if self.text != "":
            self.text += text
        else:
            self.text = text

    def _append_abilities(self):
        def format_ability(attributes: dict):
            ab = "<p><strong>{}</strong> ({})</p>".format(
                attributes.get("name"),
                attributes.get("value"),
            )
            ab += "<p>"
            for index, value in attributes.items():
                if index == "ability_checks":
                    ab += f"Ability Checks {value}<br/>"
                if index == "saving_throws":
                    ab += f"Saving Throw Checks {value}<br/>"
                if index == "skills":
                    if len(value) != 0:
                        for skill, modifier in value.items():
                            ab += f"{skill} Skill Checks {modifier}<br/>"
                if index == "carry_capacity":
                    ab += f"Carry Capacity {value}<br/>"
                if index == "push_pull_carry":
                    ab += f"Push Pull Carry Capacity {value}<br/>"
                if index == "maximum_lift":
                    ab += f"Maximum Lift Capacity {value}<br/>"
            ab += "</p>"
            return ab

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

        block = "<p><strong>ABILITY SCORES</strong></p>"
        block += format_ability(strength.attr)
        block += format_ability(dexterity.attr)
        block += format_ability(constitution.attr)
        block += format_ability(intelligence.attr)
        block += format_ability(wisdom.attr)
        block += format_ability(charisma.attr)
        return block

    def _append_features(self):
        block = "<p><strong>CLASS FEATURES</strong></p>"
        block += "<p>"
        for level, _ in self.data.get("features").items():
            for feature in _:
                block += f"{feature}<br/>"
        block += "</p>"
        return block

    @staticmethod
    def _append_list(header: str, items: list):
        items.sort()
        block = f"<p><strong>{header}</strong></p>"
        block += "<p>"
        for item in items:
            block += f"{item}<br/>"
        block += "</p>"
        return block

    def _append_magic(self):
        magic_class = list()
        for level, spells in self.data.get("magic_class").items():
            for spell in spells:
                if spell not in magic_class:
                    magic_class.append(spell)

        block = "<p><strong>Circle (Druid), Domain (Cleric), Expanded (Warlock), Oath (Paladin) Spells</strong></p>"
        block += "<p>"
        if len(magic_class) > 0:
            magic_class.sort()
            for spell in magic_class:
                block += f"{spell}<br/>"
        block += "</p>"
        return block

    def _append_proficiency(self):
        def format_proficiencies(proficiencies: OrderedDict) -> str:
            prof = ""
            for type, proficiency_list in proficiencies.items():
                prof += f"<p><strong>{type.capitalize()}</strong></p>"
                prof += "<p>"
                if isinstance(proficiency_list, list):
                    proficiency_list.sort()
                for proficiency in proficiency_list:
                    prof += f"{proficiency}<br/>"
                prof += "</p>"
            return prof

        block = "<p><strong>PROFICIENCIES</strong></p>"
        block += format_proficiencies(self.data.get("proficiency"))
        block += self._append_list("Languages", self.data.get("languages"))
        block += self._append_list("Saving Throws", self.data.get("saves"))
        block += self._append_list("Skills", self.data.get("skills"))
        return block

    def run(self, port: int = 8080) -> None:
        """
        Writes the character sheet and starts the server.

        :param int port: Character server port number. Default port is 8080.

        """

        def format_race():
            if self.data.get("subrace") != "":
                race = f'{self.data.get("race")}, {self.data.get("subrace")}'
            elif self.data.get("race") == "HalfElf":
                race = "Half-Elf"
            elif self.data.get("race") == "HalfOrc":
                race = "Half-Orc"
            elif self.data.get("race") == "Yuanti":
                race = "Yuan-ti"
            else:
                race = self.data.get("race")
            return race

        def format_size():
            size = self.data.get("size")
            hgt = self.data.get("height")
            wgt = self.data.get("weight")
            feet = math.floor(hgt / 12)
            inches = hgt % 12
            hgt = "{}' {}\"".format(feet, inches)
            wgt = f"{wgt} lbs."
            return size, hgt, wgt

        (size_class, height, weight) = format_size()
        self.body = "<!DOCTYPE html>"
        self.body = f"<html><head><title>Yari {__version__}</title></head><body>"
        self.body = "<p>"
        self.body = f"<strong>Race:</strong> {format_race()}<br/>"
        self.body = f'<strong>Sex: </strong>{self.data.get("sex")}<br/>'
        self.body = f'<strong>Alignment: </strong>{self.data.get("alignment")}<br/>'
        self.body = f'<strong>Background: </strong> {self.data.get("background")}<br/>'
        self.body = f"<strong>Height: </strong>{height}<br/>"
        self.body = f"<strong>Weight: </strong>{weight}<br/>"
        self.body = f"<strong>Size: </strong>{size_class}<br/>"
        self.body = "</p>"

        self.body = "<p>"
        self.body = f'<strong>Class: </strong>{self.data.get("class")}<br/>'
        self.body = f'<strong>Subclass: </strong>{self.data.get("subclass")}<br/>'
        self.body = f'<strong>Level: </strong>{self.data.get("level")}<br/>'
        self.body = "</p>"

        self.body = self._append_abilities()
        self.body = (
            f'<p><strong>Spell Slots: </strong>{self.data.get("spell_slots")}</p>'
        )
        self.body = self._append_proficiency()
        self.body = self._append_list("Feats", self.data.get("feats"))
        self.body = self._append_list("RACIAL TRAITS", self.data.get("traits"))
        self.body = self._append_list(
            "Innate Spellcasting", self.data.get("magic_innate")
        )
        self.body = self._append_features()
        self.body = self._append_magic()
        self.body = self._append_list("EQUIPMENT", self.data.get("equipment"))
        self.body = "</body></html>"

        async def index(request):
            print(request.headers)
            return web.Response(
                content_type="text/html",
                text=BeautifulSoup(self.body, "html.parser").prettify(),
            )

        app = web.Application()
        app.router.add_get("/", index)
        web.run_app(app, host="127.0.0.1", port=port)


def out(message: str, output_code: int = 0):
    """
    Used to output status messages to the terminal.

    :param str message: Message for output
    :param int output_code: Error code number (-2 - 2)
        -2: Info
        -1: Warning
         0: Success (Default)
         1: Error
         2: Error w/ traceback

    """
    if output_code not in range(-2, 3):
        raise ValueError("Argument 'output_code' is invalid.")
    else:
        # Error
        if output_code in (1, 2):
            click.secho(f"ERROR: {message}", bold=True, fg="red")
            # Adds traceback to error message
            if output_code == 2:
                traceback.print_exc()
            exit()
        # Warning
        elif output_code == -1:
            click.secho(f"WARN: {message}", bold=True, fg="yellow")
        # Info
        elif output_code == -2:
            click.secho(f"INFO: {message}", bold=False, fg="white")
        # Success
        else:
            click.secho(f"OK: {message}", bold=False, fg="bright_green")


if __name__ == "__main__":
    main()
