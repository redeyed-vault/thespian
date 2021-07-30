from collections import OrderedDict
from typing import Type

from .errors import Error
from .flags import MyTapestry
from .sources import Load

from aiohttp import web
from bs4 import BeautifulSoup


class _AttributeWriter:
    def __init__(self, ability, value, skills):
        self._ability = ability
        self._value = value
        self._skills = skills

    def _get_attribute_array(self):
        from math import floor

        modifier = floor((self._value - 10) / 2)
        attribute_array = dict()
        attribute_array["ability_checks"] = modifier
        attribute_array["saving_throws"] = modifier
        attribute_array["value"] = self._value

        if self._ability == "Strength":
            attribute_array["carry_capacity"] = self._value * 15
            attribute_array["push_pull_carry"] = attribute_array["carry_capacity"] * 2
            attribute_array["maximum_lift"] = attribute_array["push_pull_carry"]

        attribute_array["skills"] = list()
        for skill in self._skills:
            primary_ability = Load.get_columns(skill, "ability", source_file="skills")
            if primary_ability != self._ability:
                continue

            attribute_array["skills"].append((skill, modifier))

        return attribute_array

    @classmethod
    def write(cls, scores, skills):
        attribs = dict()
        x = None
        for attribute in tuple(scores.keys()):
            x = cls(attribute, scores.get(attribute), skills)
            attribs[attribute] = x._get_attribute_array()

        ab = ""
        for attribute, attributes in attribs.items():
            ab += f"<p><strong>{attribute}</strong> ({attributes['value']})</p>"
            ab += "<p>"
            for index, value in attributes.items():
                if index == "ability_checks":
                    ab += f"Ability Checks {value}<br/>"
                if index == "saving_throws":
                    ab += f"Saving Throw Checks {value}<br/>"
                if index == "carry_capacity":
                    ab += f"Carry Capacity {value}<br/>"
                if index == "push_pull_carry":
                    ab += f"Push Pull Carry Capacity {value}<br/>"
                if index == "maximum_lift":
                    ab += f"Maximum Lift Capacity {value}<br/>"
                if index == "skills":
                    skill_list = attributes.get("skills")
                    if len(skill_list) != 0:
                        for pair in skill_list:
                            skill, modifier = pair
                            ab += f"{skill} Skill Checks {modifier}<br/>"
            ab += "</p>"

        return ab


class HTTPD:
    def __init__(self, data: MyTapestry, port: Type[int] = 5000):
        self.data = data
        self.port = port
        self.text: str = ""

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

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

        def format_race(race, subrace):
            if subrace != "":
                race = f"{race}, {subrace}"
            elif race == "HalfElf":
                race = "Half-Elf"
            elif race == "HalfOrc":
                race = "Half-Orc"
            elif race == "Yuanti":
                race = "Yuan-ti"
            else:
                race = race
            return race

        d = self.data

        self._write = "<!DOCTYPE html>"
        self._write = "<html><head><title>Yari</title></head><body>"
        self._write = "<p>"
        self._write = f"<strong>Race:</strong> {format_race(d.race, d.subrace)}<br/>"
        self._write = f"<strong>Sex: </strong>{d.sex}<br/>"
        self._write = f"<strong>Alignment: </strong>{d.alignment}<br/>"
        self._write = f"<strong>Background: </strong> {d.background}<br/>"
        self._write = f"<strong>Height: </strong>{d.height}<br/>"
        self._write = f"<strong>Weight: </strong>{d.weight}<br/>"
        self._write = f"<strong>Size: </strong>{d.size}<br/>"
        self._write = "</p>"

        self._write = "<p>"
        self._write = f"<strong>Class: </strong>{d.klass}<br/>"
        self._write = f"<strong>Subclass: </strong>{d.subclass}<br/>"
        self._write = f"<strong>Level: </strong>{d.level}<br/>"
        self._write = "</p>"

        self._write = _AttributeWriter.write(d.scores, d.skills)

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
        """
        if not isinstance(self.data, OrderedDict):
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
        if not all(dk in self.data for dk in data_keys):
            raise ValueError(
                "All data keys 'race', 'subrace', 'sex', 'alignment', "
                "'background', 'size', 'height', 'weight', 'class', 'subclass', "
                "'level', 'bonus', 'score_array', 'saves', 'proficiency', "
                "'languages', 'magic_innate', 'spell_slots', 'skills', 'feats', "
                "'equipment', 'features', 'traits' must have a value."
            )

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
        """
