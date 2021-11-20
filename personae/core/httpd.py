from dataclasses import dataclass

from .formatting import (
    AttributeWriter,
    FeatureWriter,
    ListWriter,
    ProficiencyWriter,
    SpellWriter,
)
from .seamstress import Seamstress

from aiohttp import web
from bs4 import BeautifulSoup


@dataclass
class CharacterSheetServer:
    """Starts a local HTTP character sheet display server."""

    data: Seamstress
    port: int = 5000
    content: str = ""

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

    @property
    def _write(self):
        return self.content

    @_write.setter
    def _write(self, text: str):
        if self.content != "":
            self.content += text
        else:
            self.content = text

    def run(self):
        """Starts the HTTP server."""

        def format_race(race, subrace):
            if subrace is not None:
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
        self._write = "<html><head><title>Personae</title>"
        self._write = '<link type="text/css" rel="stylesheet" href="/css/style.css">'
        self._write = "</head><body>"
        self._write = "<h1>Character Sheet</h1>"
        self._write = "<p>"
        self._write = f"<strong>Race:</strong> {format_race(d.race, d.subrace)}<br/>"
        self._write = f"<strong>Sex: </strong>{d.sex}<br/>"
        self._write = f"<strong>Alignment: </strong>{d.alignment}<br/>"
        self._write = f"<strong>Background: </strong> {d.background}<br/>"
        feet, inches = d.height
        self._write = f"<strong>Height: </strong>{feet}' {inches}\"<br/>"
        self._write = f"<strong>Weight: </strong>{d.weight}<br/>"
        self._write = f"<strong>Size: </strong>{d.size}<br/>"
        self._write = "</p>"

        self._write = "<p>"
        self._write = f"<strong>Class: </strong>{d.klass}<br/>"
        self._write = f"<strong>Subclass: </strong>{d.subclass}<br/>"
        self._write = f"<strong>Level: </strong>{d.level}<br/>"
        self._write = "</p>"

        self._write = AttributeWriter.write(d.scores, d.skills)

        self._write = f"<p><strong>Spell Slots: </strong>{d.spellslots}</p>"

        self._write = ProficiencyWriter.write(
            d.armors,
            d.languages,
            d.level,
            d.savingthrows,
            d.scores,
            d.skills,
            d.speed,
            d.tools,
            d.weapons,
        )
        self._write = ListWriter.write("FEATS", d.feats)
        self._write = ListWriter.write("RACIAL TRAITS", d.traits)
        self._write = ListWriter.write("INNATE SPELLCASTING", d.spells)
        self._write = FeatureWriter.write(d.features)
        self._write = SpellWriter.write(d.klass, d.level, d.bonusmagic)
        self._write = ListWriter.write("EQUIPMENT", d.equipment)

        self._write = "</body></html>"

        async def character_sheet(request):
            return web.Response(
                content_type="text/html",
                text=BeautifulSoup(self._write, "html.parser").prettify(),
            )

        app = web.Application()
        app.add_routes(
            [
                web.static("/css", "personae/core/css/"),
                web.get("/", character_sheet),
            ]
        )
        web.run_app(app, host="127.0.0.1", port=self.port)
