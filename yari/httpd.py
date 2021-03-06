from collections import OrderedDict
from dataclasses import dataclass
from math import floor
from random import choice, sample, shuffle
import socket
from sys import exit
import traceback

from aiohttp import web
from bs4 import BeautifulSoup

from . import (
    get_proficiency_bonus,
    roll,
    __version__,
)


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
        _attributes = AttributeGenerator(_class.abilities, _race.bonus)
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
            primary_ability=_class.abilities,
            saves=_class.saving_throws,
            magic_innate=_race.magic_innate,
            spell_slots=_class.spell_slots,
            score_array=score_array,
            languages=_race.languages + _class.languages,
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


class YariHTTP:
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
