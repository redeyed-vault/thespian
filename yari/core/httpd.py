from .formatting import (
    AttributeWriter,
    FeatureWriter,
    ListWriter,
    ProficiencyWriter,
    SpellWriter,
)
from .seamstress import MyTapestry
from .sources import Load

from aiohttp import web
from bs4 import BeautifulSoup


class HTTPD:
    def __init__(self, data: MyTapestry, port: int = 5000):
        self.data = data
        self.port = port
        self.text = ""

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

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

        self._write = AttributeWriter.write(d.scores, d.skills)

        self._write = f"<p><strong>Spell Slots: </strong>{d.spellslots}</p>"

        self._write = ProficiencyWriter.write(
            d.armors, d.languages, d.savingthrows, d.skills, d.tools, d.weapons
        )
        self._write = ListWriter.write("FEATS", d.feats)
        self._write = ListWriter.write("RACIAL TRAITS", d.traits)
        self._write = ListWriter.write("INNATE SPELLCASTING", d.spells)
        self._write = FeatureWriter.write(d.features)
        self._write = SpellWriter.write(d.klass, d.level, d.bonusmagic)
        self._write = ListWriter.write("EQUIPMENT", d.equipment)

        self._write = "</body></html>"

        async def index(request):
            return web.Response(
                content_type="text/html",
                text=BeautifulSoup(self._write, "html.parser").prettify(),
            )

        app = web.Application()
        app.router.add_get("/", index)
        web.run_app(app, host="127.0.0.1", port=port)
