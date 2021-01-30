from collections import OrderedDict
from dataclasses import dataclass
from math import floor
from random import choice, sample, shuffle
import socket
from sys import exit
import traceback

from aiohttp import web
from bs4 import BeautifulSoup
import click

from . import (
    PC_BACKGROUNDS,
    PC_CLASSES,
    PC_FEATS,
    PC_GENDERS,
    PC_LANGUAGES,
    PC_RACES,
    PC_SKILLS,
    PC_SUBCLASSES,
    PC_SUBRACES,
    PC_TOOLS,
    Aasimar,
    Bugbear,
    Dragonborn,
    Dwarf,
    Elf,
    Firbolg,
    Gith,
    Gnome,
    Goblin,
    Goliath,
    Halfling,
    HalfElf,
    HalfOrc,
    Hobgoblin,
    Human,
    Kenku,
    Kobold,
    Lizardfolk,
    Orc,
    Tabaxi,
    Tiefling,
    Triton,
    Yuanti,
    Barbarian,
    Bard,
    Cleric,
    Druid,
    Fighter,
    Monk,
    Paladin,
    Ranger,
    Rogue,
    Sorcerer,
    Warlock,
    Wizard,
    Strength,
    Dexterity,
    Constitution,
    Intelligence,
    Wisdom,
    Charisma,
    Load,
    get_all_languages,
    get_all_skills,
    get_default_background,
    get_proficiency_bonus,
    get_subclasses_by_class,
    get_subraces_by_race,
    roll,
    __version__,
)


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
    # Checks to see if address is already being used
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = ("127.0.0.1", port)
    host, port = location
    if conn.connect_ex(location) == 0:
        out(
            f"Address {host}:{port} is already in use. Please use another port with the '-port=<DIFFERENT_PORT>' argument or close the process currently associated with this address.",
            1,
        )
    conn.close()

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

    # Handle application argument processing.
    if race not in PC_RACES:
        out(f"invalid character race '{race}'.", 1)

    if klass not in PC_CLASSES:
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
        if sex in PC_GENDERS:
            sex = sex
        else:
            sex = choice(PC_GENDERS)

        subraces_by_race = [s for s in get_subraces_by_race(race)]
        if subrace == "":
            if len(subraces_by_race) != 0:
                subrace = choice(subraces_by_race)
        else:
            try:
                # Race has no subraces
                if len(subraces_by_race) == 0:
                    raise ValueError(f"'{race}' has no available subraces.")

                # Race has subraces but invalid one chosen
                if subrace not in subraces_by_race:
                    raise ValueError(f"'{subrace}' is not a subrace of '{race}'.")
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
            if background not in PC_BACKGROUNDS:
                out(f"invalid character background '{background}'.", 1)

        valid_class_subclasses = get_subclasses_by_class(klass)
        if subclass == "":
            subclass = choice(valid_class_subclasses)
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
        _attributes = AttributeGenerator(_class.primary_ability, _race.bonus)
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
    threshold: int = 65

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
        # First, assign highest values to class specific abilities
        for ability in tuple(self.primary_ability.values()):
            value = max(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)
            out(f"Result of {value} assigned to ability '{ability}'.", -2)

        # Assign remaining abilities
        for _ in range(0, 4):
            ability = choice(ability_choices)
            value = choice(generated_scores)
            score_array[ability] = value
            ability_choices.remove(ability)
            generated_scores.remove(value)
            out(f"Result of {value} assigned to ability '{ability}'.", -2)

        # Finally, apply any applicable racial bonuses
        for ability, bonus in self.racial_bonus.items():
            value = score_array.get(ability) + bonus
            score_array[ability] = value
            out(
                f"Racial bonus of {bonus} applied to '{ability}'. Score is now {value}.",
                -2,
            )

        return score_array


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
                self.skills = self.skills + sample(cavalier_skills, 1)
            elif self.subclass == "College of Lore":
                lore_skills = [x for x in get_all_skills() if x not in self.skills]
                self.skills = self.skills + sample(lore_skills, 3)
            elif self.subclass == "Samurai":
                proficiency_choice = choice(("Language", "Skill"))
                if proficiency_choice == "Language":
                    samurai_language = [
                        x for x in get_all_languages() if x not in self.languages
                    ]
                    self.languages = self.languages + sample(samurai_language, 1)
                elif proficiency_choice == "Skill":
                    samurai_skills = [
                        "History",
                        "Insight",
                        "Performance",
                        "Persuasion",
                    ]
                    samurai_skills = [s for s in samurai_skills if s not in self.skills]
                    self.skills = self.skills + sample(samurai_skills, 1)
            elif self.subclass == "Way of the Drunken Master":
                self.skills.append("Performance")

    def _add_feat(self) -> None:
        """Randomly selects and adds a valid feats."""
        feats = [feat for feat in list(PC_FEATS) if feat not in self.feats]
        shuffle(feats)
        feat_choice = feats.pop()
        out(f"Checking prerequisites for '{feat_choice}'...", -2)
        # Keep choosing a feat until prerequisites met
        if not self._has_required(feat_choice):
            out(f"Prerequisites not met for '{feat_choice}'.", -1)
            while not self._has_required(feat_choice):
                shuffle(feats)
                feat_choice = feats.pop()
                out(f"Checking prerequisites for '{feat_choice}'...", -2)
                if not self._has_required(feat_choice):
                    out(f"Prerequisites not met for '{feat_choice}'.", -1)
        # Prerequisites met, inform, add to list and apply features
        out(f"Prerequisites met for '{feat_choice}'.")
        self._add_feat_perks(feat_choice)
        self.feats.append(feat_choice)

    def _add_feat_perks(self, feat: str) -> None:
        """
        Assign associated features by specified feat

        :param str feat: Feat to add features for

        """

        def get_feat_perks(feat_name: str) -> (dict, None):
            """Get perks for a feat by feat_name."""
            return Load.get_columns(feat_name, "perk", source_file="feats")

        def has_one(keys: tuple, iterable: tuple) -> bool:
            """Returns True if at least one key is found in iterable."""
            for x in keys:
                if x in iterable:
                    return True
            return False

        # Retrieve all perks for the chosen feat
        perks = get_feat_perks(feat)

        # Feat "ability" perk
        if perks.get("ability") is not None:
            # Retrieve bonus abilities by feat
            feat_ability_options = tuple(perks.get("ability").keys())

            # If Resilient feat selected, treat a upgrade differently
            # Feat offers only one ability option
            # Otherwise feat offers multiple ability options
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
                # Set feat ability score
                # Add ability to proficient saving throws
                ability = sample(resilient_saves, 1)
                self._set_feat_ability(ability)
                self.saves = self.saves + ability
                # Updated Resilient listing with appropriate ability
                # self.feats.remove(feat)
                # self.feats.append(f"{feat} ({ability})")
            elif len(feat_ability_options) == 1:
                chosen_ability = feat_ability_options[0]
                self._set_feat_ability([chosen_ability])
            else:
                # Retrieve primary, secondary class abilities
                class_abilities = tuple(self.primary_ability.values())
                # Store the chosen ability value
                chosen_ability = None
                # If at least one class ability in feat ability options
                # Otherwise just randomly choose one ability
                if has_one(class_abilities, feat_ability_options):
                    for ability in class_abilities:
                        # Ability is one of the feat ability perk options
                        # If ability is adjustable, adjust score
                        # Otherwise, keep it movin'
                        if ability in feat_ability_options:
                            if self._is_adjustable(ability):
                                chosen_ability = ability
                                self._set_feat_ability([chosen_ability])
                                break
                            else:
                                continue
                else:
                    chosen_ability = sample(feat_ability_options, 1)
                    self._set_feat_ability(chosen_ability)

                # If Squat Nimbleness feat chosen
                # Append Athletics skill if Strength chosen
                # Append Acrobatics skill if Dexterity chosen
                # If Strength or Dexterity not class abilities, just choose one
                if feat == "Squat Nimbleness":
                    perk_skills = get_feat_perks(feat).get("skills")
                    chosen_skill = None
                    if "Strength" in class_abilities:
                        chosen_skill = perk_skills[1]
                        self._add_skill(chosen_skill)
                    elif "Dexterity" in class_abilities:
                        chosen_skill = perk_skills[0]
                        self._add_skill(chosen_skill)
                    else:
                        chosen_ability = choice(("Strength", "Dexterity"))
                        if chosen_ability == "Strength":
                            chosen_skill = perk_skills[1]
                            self._add_skill(chosen_skill, perk_skills[0])
                        else:
                            chosen_skill = perk_skills[0]
                            self._add_skill(chosen_skill, perk_skills[1])

        # Feat "language" perk
        if perks.get("language") is not None:
            # Add bonus languages based on feat
            # Add 3 if Linguist feat
            # Add 1 otherwise
            bonus_languages = perks.get("language")
            bonus_languages = [
                x for x in bonus_languages if x not in self.languages
            ]
            if feat == "Linguist":
                self.languages + sample(bonus_languages, 3)
            else:
                self.languages + sample(bonus_languages, 1)

        # Feat "proficiency" perk
        if perks.get("proficiency") is not None:
            proficiency_categories = perks.get("proficiency")
            # Armor category, append bonus proficiencies
            # Tool category, append bonus proficiencies
            if "armors" in proficiency_categories:
                self.armor_proficiency = (
                    self.armor_proficiency + proficiency_categories.get("armors")
                )
            elif "tools" in proficiency_categories:
                tool_choice = [
                    x
                    for x in proficiency_categories.get("tools")
                    if x not in self.tool_proficiency
                ]
                self.tool_proficiency.append(choice(tool_choice))
            elif "weapons" in proficiency_categories:

                def get_all_weapons():
                    all_weapons = list()
                    weapons = proficiency_categories.get("weapons")
                    # User has simple weapon proficiencies
                    # Remove all simple weapons from list
                    if "Simple" in self.weapon_proficiency:
                        del weapons["Simple"]

                    # Make an exclusion of non-simple weapons
                    # Make an exclusion of non-martial weapons
                    excluded_weapons = [
                        x
                        for x in self.weapon_proficiency
                        if x != "Simple" and x != "Martial"
                    ]

                    for category, _ in weapons.items():
                        for weapon in weapons.get(category):
                            all_weapons.append(weapon)

                    return all_weapons

                weapons = [x for x in get_weapon_chest()]
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
                    selections = selections.get("Martial") + selections.get(
                        "Simple"
                    )
                    selections = [
                        selection
                        for selection in selections
                        if selection not in self.weapon_proficiency
                    ]

                self.weapon_proficiency = self.weapon_proficiency + sample(
                    selections, 4
                )
                selections.clear()

        # Feat "resistance" perk
        if perks.get("resistance") is not None:
            pass

        # Feat "skills" perk
        if perks.get("skills") is not None:
            pass

        # Feat "spells" perk
        if perks.get("spells") is not None:
            spells = perks.get("spells")
            for spell in spells:
                if isinstance(spell, list):
                    self.magic_innate.append(choice(spell))
                else:
                    self.magic_innate.append(spell)

    def _add_skill(self, skill: str, alternate_skill: str = None) -> bool:
        """Adds skill or alternate_skill to skill list, (if applicable)."""
        try:
            if skill not in self.skills:
                self.skills.append(skill)
            elif alternate_skill is not None:
                if alternate_skill not in self.skills:
                    self.skills.append(alternate_skill)
                else:
                    raise ValueError("Neither valid skills available")
            return True
        except ValueError:
            return False

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
            ability_upgrades = floor(num_of_upgrades * percentage / 100.0)
            feat_upgrades = num_of_upgrades - ability_upgrades
            return ability_upgrades, feat_upgrades

    def _has_required(self, feat: str) -> bool:
        """
        Determines if character has the prerequisites for feat.

        :param str feat: Feat to check prerequisites for.

        """
        # Character already has feat
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
        # Chosen feat is "Armor Related" or Weapon Master but already proficient w/ assoc. armor type.
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

        def get_feat_requirements(
            feat_name: str, use_local: bool = True
        ) -> (dict, None):
            """Returns all requirements for feat_name."""
            return Load.get_columns(
                feat_name, "required", source_file="feats", use_local=use_local
            )

        # Go through ALL prerequisites.
        prerequisite = get_feat_requirements(feat)
        for requirement, _ in prerequisite.items():
            # Ignore requirements that are None
            if prerequisite.get(requirement) is None:
                continue

            # Check ability requirements
            if requirement == "ability":
                for ability, required_score in prerequisite.get(requirement).items():
                    my_score = self.score_array[ability]
                    if my_score < required_score:
                        return False

            # Check caster requirements
            if requirement == "caster":
                # If caster prerequisite True
                if prerequisite.get(requirement):
                    # Check if character has spellcasting ability
                    if self.spell_slots == "0":
                        return False

                    # Magic Initiative class check
                    if feat == "Magic Initiative" and self.klass not in (
                        "Bard",
                        "Cleric",
                        "Druid",
                        "Sorcerer",
                        "Warlock",
                        "Wizard",
                    ):
                        return False

                    # Ritual Caster class check
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

            # Check proficiency requirements
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

            # Check race requirements
            if requirement == "race":
                if self.race not in prerequisite.get(requirement):
                    return False

            # Check subrace requirements
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

            # If one ability specified, apply a +2 bonus
            if len(ability_array) == 1:
                bonus = 2
            # If two abilities specified, apply a +1 bonus
            elif len(ability_array) == 2:
                bonus = 1
            # Otherwise raise error
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
                    out(f"Ability Score Improvement: '{ability}' set to {value}.", -2)
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

        def set_ability_score(scores: OrderedDict, ability_name: str):
            # Adjusts the ability score by 1 point
            value = scores.get(ability_name) + 1
            scores[ability_name] = value
            out(f"Feat ability adjustment: '{ability_name}' set to {value}.", -2)

        try:
            # Ensure score_array object is type OrderedDict
            if not isinstance(self.score_array, OrderedDict):
                raise TypeError("Object 'scores' is not type 'OrderedDict'.")

            # If only one ability option available
            if len(ability_options) == 1:
                set_ability_score(self.score_array, ability_options[0])
                return

            is_upgraded = False
            primary_ability = list(self.primary_ability.values())

            # Choose primary ability over other options (if applicable)
            for ability in primary_ability:
                if ability in ability_options:
                    if self._is_adjustable(ability):
                        set_ability_score(self.score_array, ability)
                        is_upgraded = True
                        break
                    else:
                        ability_options.remove(ability)

            # Choose any one ability option if not upgraded above
            if not is_upgraded:
                set_ability_score(self.score_array, choice(ability_options))
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

                    bonus_type = choice([1, 2])
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
        armor_chest[armor_category] = Load.get_columns(
            armor_category, source_file="armors"
        )
    yield armor_chest


def get_tool_chest():
    """Returns a full collection of tools."""
    for main_tool in PC_TOOLS:
        if main_tool in ("Artisan's tools", "Gaming set", "Musical instrument"):
            for sub_tool in Load.get_columns(main_tool, source_file="tools"):
                yield f"{main_tool} - {sub_tool}"
        else:
            yield main_tool


def get_weapon_chest():
    """Returns a full collection of weapons."""
    weapon_chest = dict()
    for weapon_category in ("Simple", "Martial"):
        weapon_chest[weapon_category] = Load.get_columns(
            weapon_category, source_file="weapons"
        )
    yield weapon_chest


class HTTPServer:
    def __init__(self, data: OrderedDict):
        self.data = data
        self.text: str = ""

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

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

    @property
    def _write(self):
        return self.text

    @_write.setter
    def _write(self, text: str):
        if self.text != "":
            self.text += text
        else:
            self.text = text

    def run(self, port: int = 8080) -> None:
        """
        Starts the HTTP character server.

        :param int port: Character server port number. Default port is 8080.

        """
        if not isinstance(self.data, OrderedDict):
            raise TypeError("Argument 'data' must be of type 'OrderedDict'.")

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
            feet = floor(hgt / 12)
            inches = hgt % 12
            hgt = "{}' {}\"".format(feet, inches)
            wgt = f"{wgt} lbs."
            return size, hgt, wgt

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
        if not all(dk in self.data for dk in data_keys):
            raise ValueError(
                "All data keys 'race', 'subrace', 'sex', 'alignment', "
                "'background', 'size', 'height', 'weight', 'class', 'subclass', "
                "'level', 'bonus', 'score_array', 'saves', 'proficiency', "
                "'languages', 'magic_innate', 'spell_slots', 'skills', 'feats', "
                "'equipment', 'features', 'traits' must have a value."
            )

        (size_class, height, weight) = format_size()
        self._write = "<!DOCTYPE html>"
        self._write = f"<html><head><title>Yari {__version__}</title></head><body>"
        self._write = "<p>"
        self._write = f"<strong>Race:</strong> {format_race()}<br/>"
        self._write = f'<strong>Sex: </strong>{self.data.get("sex")}<br/>'
        self._write = f'<strong>Alignment: </strong>{self.data.get("alignment")}<br/>'
        self._write = (
            f'<strong>Background: </strong> {self.data.get("background")}<br/>'
        )
        self._write = f"<strong>Height: </strong>{height}<br/>"
        self._write = f"<strong>Weight: </strong>{weight}<br/>"
        self._write = f"<strong>Size: </strong>{size_class}<br/>"
        self._write = "</p>"

        self._write = "<p>"
        self._write = f'<strong>Class: </strong>{self.data.get("class")}<br/>'
        self._write = f'<strong>Subclass: </strong>{self.data.get("subclass")}<br/>'
        self._write = f'<strong>Level: </strong>{self.data.get("level")}<br/>'
        self._write = "</p>"

        self._write = self._append_abilities()
        self._write = (
            f'<p><strong>Spell Slots: </strong>{self.data.get("spell_slots")}</p>'
        )
        self._write = self._append_proficiency()
        self._write = self._append_list("Feats", self.data.get("feats"))
        self._write = self._append_list("RACIAL TRAITS", self.data.get("traits"))
        self._write = self._append_list(
            "Innate Spellcasting", self.data.get("magic_innate")
        )
        self._write = self._append_features()
        self._write = self._append_magic()
        self._write = self._append_list("EQUIPMENT", self.data.get("equipment"))
        self._write = "</body></html>"

        async def index(request):
            print(request.headers)
            return web.Response(
                content_type="text/html",
                text=BeautifulSoup(self._write, "html.parser").prettify(),
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
