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
    def write(cls, scores: dict, skills: list):
        attribs = dict()
        x = None
        for attribute in tuple(scores.keys()):
            x = cls(attribute, scores.get(attribute), skills)
            attribs[attribute] = x._get_attribute_array()

        block = ""
        for attribute, attributes in attribs.items():
            block += f"<p><strong>{attribute}</strong> ({attributes['value']})</p>"
            block += "<p>"
            for index, value in attributes.items():
                if index == "ability_checks":
                    block += f"Ability Checks {value}<br/>"
                if index == "saving_throws":
                    block += f"Saving Throw Checks {value}<br/>"
                if index == "carry_capacity":
                    block += f"Carry Capacity {value}<br/>"
                if index == "push_pull_carry":
                    block += f"Push Pull Carry Capacity {value}<br/>"
                if index == "maximum_lift":
                    block += f"Maximum Lift Capacity {value}<br/>"
                if index == "skills":
                    skill_list = attributes.get("skills")
                    if len(skill_list) != 0:
                        for pair in skill_list:
                            skill, modifier = pair
                            block += f"{skill} Skill Checks {modifier}<br/>"
            block += "</p>"

        return block


class _FeatureWriter:
    def __init__(self, features: dict):
        self._features = features

    def _format_features(self):
        for _, features in self._features.items():
            if type(features) is list:
                features.sort()

        return self._features

    @classmethod
    def write(cls, features: dict):
        x = cls(features)
        x._format_features()

        block = "<p><strong>CLASS FEATURES</strong></p>"

        block += "<p>"
        for level, features in x._features.items():
            for feature in features:
                block += f"{level}.) {feature}<br/>"
        block += "</p>"

        return block


class _ListWriter:
    def __init__(self, header: str, items: list):
        self._header = header
        self._items = items

    @classmethod
    def write(cls, header: str, items: list):
        x = cls(header, items)
        block = f"<p><strong>{header}</strong></p>"

        if len(items) != 0:
            items.sort()
            block += "<p>"
            for item in items:
                block += f"{item}<br/>"
            block += "</p>"
        else:
            block += "<p></p>"

        return block


class _ProficiencyWriter:
    def __init__(self, armors, languages, saving_throws, skills, tools, weapons):
        self._armors = armors
        self._languages = languages
        self._saving_throws = saving_throws
        self._skills = skills
        self._tools = tools
        self._weapons = weapons

    def _sort_proficiencies(self):
        for this_list in (
            self._armors,
            self._tools,
            self._weapons,
            self._languages,
            self._saving_throws,
            self._skills,
        ):
            this_list.sort()

        return {
            "armors": self._armors,
            "tools": self._tools,
            "weapons": self._weapons,
            "languages": self._languages,
            "saving_throws": self._saving_throws,
            "skills": self._skills,
        }

    @classmethod
    def write(cls, armors, languages, saving_throws, skills, tools, weapons):
        x = cls(armors, languages, saving_throws, skills, tools, weapons)
        types = x._sort_proficiencies()

        block = "<p><strong>PROFICIENCIES</strong></p>"

        for object_type in (
            "armors",
            "tools",
            "weapons",
            "languages",
            "saving_throws",
            "skills",
        ):
            block += f"<p><strong>{object_type.capitalize()}</strong></p>"
            block += "<p>"
            for obj in types.get(object_type):
                block += f"{obj}<br/>"
            block += "</p>"

        return block


class HTTPD:
    def __init__(self, data: MyTapestry, port: int = 5000):
        self.data = data
        self.port = port
        self.text = ""

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

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

        self._write = f"<p><strong>Spell Slots: </strong>{d.spellslots}</p>"

        self._write = _ProficiencyWriter.write(
            d.armors, d.languages, d.savingthrows, d.skills, d.tools, d.weapons
        )

        self._write = _ListWriter.write("FEATS", d.feats)

        self._write = _ListWriter.write("RACIAL TRAITS", d.traits)

        self._write = _ListWriter.write("INNATE SPELLCASTING", d.spells)

        self._write = _FeatureWriter.write(d.features)

        # Placeholder for bonus magic

        self._write = _ListWriter.write("EQUIPMENT", d.equipment)

        self._write = "</body></html>"

        async def index(request):
            return web.Response(
                content_type="text/html",
                text=BeautifulSoup(self._write, "html.parser").prettify(),
            )

        app = web.Application()
        app.router.add_get("/", index)
        web.run_app(app, host="127.0.0.1", port=port)
        """
        self._write = self._append_magic()
        """
