from argparse import ArgumentParser

from .dice import AttributeGenerator
from .httpd import HTTPd
from .levelup import AbilityScoreImprovement
from .seamstress import (
    RaceSeamstress,
    ClassSeamstress,
    MyTapestry,
)
from .sources import Load
from .utils import (
    get_character_classes,
    get_character_races,
    prompt,
    _e,
)


def main():
    app = ArgumentParser(
        prog="YARI", description="A Dungeons & Dragons 5e character generator."
    )
    app.add_argument(
        "-race",
        "-r",
        help="sets character's race",
        required=True,
        type=str,
        choices=get_character_races(),
        default="Human",
    )
    app.add_argument(
        "-klass",
        "-k",
        help="sets character's class",
        type=str,
        choices=get_character_classes(),
        default="Fighter",
    )
    app.add_argument(
        "-sex",
        "-s",
        help="sets character's sex",
        type=str,
        choices=("Female", "Male"),
        default="Female",
    )
    app.add_argument(
        "-port",
        "-p",
        help="sets HTTP server port",
        type=int,
        default=8080,
    )
    args = app.parse_args()
    race = args.race
    klass = args.klass
    sex = args.sex
    port = args.port

    # Generate racial and class attributes
    a = RaceSeamstress(race, sex)
    b = ClassSeamstress(klass, a.data)

    # Run Attribute generator
    a.data["scores"] = AttributeGenerator(
        b.data.get("ability"), a.data.get("bonus")
    ).roll()

    c = MyTapestry()
    c.weave_tapestry(a.data, b.data)

    d = c.view(True)
    # Run Ability Score Improvement generator
    u = AbilityScoreImprovement(
        armors=d["armors"],
        feats=[],
        klass=d["klass"],
        languages=d["languages"],
        level=d["level"],
        race=d["race"],
        resistances=d["resistances"],
        saves=d["savingthrows"],
        scores=d["scores"],
        skills=d["skills"],
        spells=d["spells"],
        spellslots=d["spellslots"],
        subclass=d["subclass"],
        subrace=d["subrace"],
        tools=d["tools"],
        weapons=d["weapons"],
    )
    u.run()

    d["armors"] = u.armors
    d["feats"] = u.feats
    d["languages"] = u.languages
    d["scores"] = u.scores
    d["spells"] = u.spells
    """
    self.resistances = u.resistances
    self.tools = u.tools
    self.weapons = u.weapons
    """

    try:
        with HTTPd(c.view(), port) as http:
            http.run()
    except (OSError, TypeError, ValueError) as e:
        exit(e)
