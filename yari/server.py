from collections import OrderedDict

from aiohttp import web
from bs4 import BeautifulSoup

from yari.attributes import (
    Charisma,
    Constitution,
    Dexterity,
    Intelligence,
    Strength,
    Wisdom,
)
from yari.version import __version__


class CharacterServer:
    """
    Creates the CharacterServer object.

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
            "class",
            "subclass",
            "level",
            "bonus",
            "score_array",
            "saves",
            "proficiency",
            "languages",
            "spell_slots",
            "skills",
            "feats",
            "equipment",
            "features",
            "traits",
        )
        if not all(k in data for k in data_keys):
            raise ValueError(
                "All data keys 'race', 'subrace', 'sex', "
                "'alignment', 'background', 'size', 'class', 'subclass', "
                "'level', 'bonus', 'score_array', 'saves', 'proficiency', "
                "'languages', 'spell_slots', 'skills', 'feats', "
                "'equipment', 'features', 'traits' must have a value."
            )
        else:
            self.data = data
        self.text = ""

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, traceback) -> None:
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
            block = '<ability label="{}" value="{}">'.format(
                attributes.get("name"),
                attributes.get("value"),
            )
            for index, value in attributes.items():
                if index == "ability_checks":
                    block += f'<entry label="Ability Checks" value="{value}"/>'
                if index == "saving_throws":
                    block += f'<entry label="Saving Throw Checks" value="{value}"/>'
                if index == "skills":
                    if len(value) != 0:
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

        self.body = "<abilities>"
        self.body = format_ability(strength.attr)
        self.body = format_ability(dexterity.attr)
        self.body = format_ability(constitution.attr)
        self.body = format_ability(intelligence.attr)
        self.body = format_ability(wisdom.attr)
        self.body = format_ability(charisma.attr)
        self.body = "</abilities>"

    def _append_equipment(self):
        equipment = self.data.get("equipment")
        equipment.sort()
        self.body = "<equipment>"
        for item in equipment:
            self.body = f'<entry label="equipment" value="{item}" />'
        self.body = "</equipment>"

    def _append_feats(self):
        feats = self.data.get("feats")
        feats.sort()
        self.body = "<feats>"
        for feat in feats:
            self.body = f'<entry label="feat" value="{feat}" />'
        self.body = "</feats>"

    def _append_features(self):
        self.body = "<features>"
        for level, _ in self.data.get("features").items():
            for feature in _:
                self.body = f'<entry label="{self.data.get("class")} Feature" level="{level}" name="{feature}" />'
        self.body = "</features>"

    def _append_proficiency(self):
        def format_languages(languages: list) -> str:
            languages.sort()
            block = ""
            for language in languages:
                block += f'<entry label="language" value="{language}" />'
            return block

        def format_proficiencies(proficiencies: OrderedDict) -> str:
            block = ""
            for type, proficiency_list in proficiencies.items():
                block += f"<{type}>"
                if isinstance(proficiency_list, list):
                    proficiency_list.sort()
                for proficiency in proficiency_list:
                    block += f'<entry label="proficiency" value="{proficiency}" />'
                block += f"</{type}>"
            return block

        self.body = "<proficiencies>"
        self.body = f'<proficiency>{self.data.get("bonus")}</proficiency>'
        self.body = format_proficiencies(self.data.get("proficiency"))
        self.body = (
            f'<languages>{format_languages(self.data.get("languages"))}</languages>'
        )

        saves = self.data.get("saves")
        saves.sort()
        self.body = "<saving_throws>"
        for save in saves:
            self.body = f'<entry label="save" value="{save}" />'
        self.body = "</saving_throws>"

        skills = self.data.get("skills")
        skills.sort()
        self.body = "<skills>"
        for skill in skills:
            self.body = f'<entry label="skill" value="{skill}" />'
        self.body = "</skills>"
        self.body = "</proficiencies>"

    def _append_traits(self, race: str, level: int):
        self.body = "<traits>"
        for trait in self.data.get("traits"):
            if len(trait) == 1:
                self.body = f'<entry label="{race} Trait" name="{trait[0]}" />'
            else:
                (name, value) = trait
                if isinstance(value, list):
                    if (
                        name
                        in (
                            "Celestial Legacy",
                            "Drow Magic",
                            "Duergar Magic",
                            "Firbolg Magic",
                            "Githyanki Psionics",
                            "Githzerai Psionics",
                            "Innate Spellcasting",
                        )
                        or name.startswith("Legacy of")
                    ):
                        value = [val[1] for val in value]
                        value = ", ".join(value)
                    elif name in (
                        "Bite",
                        "Breath Weapon",
                        "Cantrip",
                        "Cat's Claws",
                        "Cat's Talent",
                        "Celestial Resistance",
                        "Damage Resistance",
                        "Drow Weapon Training",
                        "Duergar Resilience",
                        "Dwarven Armor Training",
                        "Dwarven Combat Training",
                        "Dwarven Resilience",
                        "Elf Weapon Training",
                        "Extra Language",
                        "Feline Agility",
                        "Fey Ancestry",
                        "Hellish Resistance",
                        "Hunter's Lore",
                        "Keen Senses",
                        "Kenku Training",
                        "Martial Prodigy (Armor)",
                        "Martial Prodigy (Weapon)",
                        "Martial Training (Armor)",
                        "Martial Training (Weapon)",
                        "Menacing",
                        "Mental Discipline",
                        "Natural Armor",
                        "Natural Athlete",
                        "Natural Illusionist",
                        "Necrotic Resistance",
                        "Sea Elf Training",
                        "Skill Versatility",
                        "Sneaky",
                        "Stout Resilience",
                        "Tinker",
                        "Tool Proficiency",
                    ):
                        value = ", ".join(value)
                    self.body = (
                        f'<entry label="{race} Trait" name="{name}" value="{value}" />'
                    )
                else:
                    if name.startswith("Necrotic") or name.startswith("Radiant"):
                        if level >= value:
                            self.body = f'<entry label="{race} Trait" name="{name}" />'
                    else:
                        self.body = f'<entry label="{race} Trait" name="{name}" value="{value}" />'
        self.body = "</traits>"

    def run(self, port: int = 8080) -> None:
        """
        Writes the character sheet and starts the server.

        :param int port: Character server port number. Default port is 8080.

        """
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

        self.body = '<?xml version="1.0"?><yari>'
        self.body = f"<meta><version>{__version__}</version></meta>"
        self.body = f"<character><race>{race}</race>"
        self.body = f'<sex>{self.data.get("sex")}</sex>'
        self.body = f'<size>{self.data.get("size")}</size>'
        self.body = f'<alignment>{self.data.get("alignment")}</alignment>'
        self.body = f'<background>{self.data.get("background")}</background>'
        self.body = f'<class>{self.data.get("class")}</class>'
        self.body = f'<subclass>{self.data.get("subclass")}</subclass>'
        self.body = f'<level>{self.data.get("level")}</level>'
        self._append_abilities()
        self.body = f'<spell_slots>{self.data.get("spell_slots")}</spell_slots>'
        self._append_proficiency()
        self._append_feats()
        self._append_equipment()
        self._append_traits(race, self.data.get("level"))
        self._append_features()
        self.body = "</character></yari>"

        async def character_sheet(request):
            return web.Response(
                content_type="text/xml", text=BeautifulSoup(self.body, "xml").prettify()
            )

        app = web.Application()
        app.router.add_get("/", character_sheet)
        web.run_app(app, host="127.0.0.1", port=port)
