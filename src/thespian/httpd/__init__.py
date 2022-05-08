from math import ceil
import os

from aiohttp import web
import aiohttp_jinja2
import jinja2

from attributes import get_ability_modifier
from sourcetree.utils import get_skill_ability, get_skill_list


class Server:
    def __init__(self, data, port=5000):
        self.data = data
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

    def run(self) -> None:
        routes = web.RouteTableDef()
        routes.static("/css", "src/thespian/httpd/css/")

        @routes.get("/")
        @aiohttp_jinja2.template("index.html")
        async def index(request: web.Request):
            d = self.data
            feet, inches = d.height
            proficiency_bonus = ceil(1 + (d.level / 4))
            features = list()
            for _, feature in d.features.items():
                features += feature
            return {
                "race": d.race,
                "ancestry": d.ancestry,
                "subrace": d.subrace,
                "sex": d.sex,
                "alignment": d.alignment,
                "background": d.background,
                "feet": feet,
                "inches": inches,
                "weight": d.weight,
                "size": d.size,
                "class": d.klass,
                "subclass": d.subclass,
                "level": d.level,
                "hit_points": d.hit_points,
                "proficiency_bonus": proficiency_bonus,
                "strength": AttributeWriter.out("Strength", d.scores, d.skills),
                "dexterity": AttributeWriter.out("Dexterity", d.scores, d.skills),
                "constitution": AttributeWriter.out("Constitution", d.scores, d.skills),
                "intelligence": AttributeWriter.out("Intelligence", d.scores, d.skills),
                "wisdom": AttributeWriter.out("Wisdom", d.scores, d.skills),
                "charisma": AttributeWriter.out("Charisma", d.scores, d.skills),
                "speed": d.speed,
                "initiative": get_ability_modifier("Dexterity", d.scores),
                "armors": d.armors,
                "tools": d.tools,
                "weapons": d.weapons,
                "languages": d.languages,
                "saves": d.saves,
                "skills": expand_skills(d.skills, d.scores, proficiency_bonus),
                "feats": d.feats,
                "traits": d.traits,
                "features": features,
                "spell_slots": d.spell_slots,
                "bonus_magic": d.bonus_magic,
                "spells": d.spells,
                "equipment": d.equipment,
            }

        app = web.Application()
        app.add_routes(routes)
        aiohttp_jinja2.setup(
            app,
            loader=jinja2.FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "templates")
            ),
        )
        web.run_app(app, host="127.0.0.1", port=self.port)


class AttributeWriter:
    """Formats and prints attribute properties."""

    def __init__(self, attribute: str, scores: dict, skills: list):
        self.attribute = attribute
        self.scores = scores
        self.skills = skills
        self.properties = dict()

        # Strength has three other unique properties.
        if attribute == "Strength":
            strength_score = self.scores[attribute]
            self.properties["carry_capacity"] = strength_score * 15
            self.properties["push_pull_carry"] = self.properties["carry_capacity"] * 2
            self.properties["maximum_lift"] = self.properties["push_pull_carry"]

    @classmethod
    def out(cls, attribute, scores, skills) -> dict:
        o = cls(attribute, scores, skills)
        properties = {
            "score": o.scores[o.attribute],
            "modifier": get_ability_modifier(o.attribute, o.scores),
            "skills": o.skills,
        }

        if len(o.properties) > 0:
            properties["properties"] = o.properties

        return properties


def expand_skills(skills: list, scores: dict, proficiency_bonus: int = 2):
    """Creates expanded skill list."""
    expanded_skills = dict()
    for skill in get_skill_list():
        ability = get_skill_ability(skill)
        modifier = get_ability_modifier(ability, scores)

        if skill in skills:
            rank = proficiency_bonus + modifier
            class_skill = True
        else:
            rank = modifier
            class_skill = False

        expanded_skills[skill] = {
            "ability": ability,
            "rank": rank,
            "is_class_skill": class_skill,
        }

    return expanded_skills
