from argparse import ArgumentParser

from .dice import AttributeGenerator
from .httpd import CharacterSheetServer
from .levelup import AbilityScoreImprovement
from .seamstress import (
    RaceSeamstress,
    ClassSeamstress,
    MyTapestry,
)
from .utils import (
    get_character_classes,
    get_character_races,
)


def main():
    app = ArgumentParser(
        description="Generate 5th edition Dungeons & Dragons characters."
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
        default=5000,
    )
    args = app.parse_args()
    race = args.race
    klass = args.klass
    sex = args.sex
    port = args.port

    a = RaceSeamstress(race, sex)
    b = ClassSeamstress(klass, a.data)

    a.data["scores"] = AttributeGenerator(
        b.data.get("ability"), a.data.get("bonus")
    ).roll()

    c = MyTapestry()
    c.weave(a.data, b.data)

    u = AbilityScoreImprovement(c.view(True))
    u.run()

    with CharacterSheetServer(c.view(), port) as http:
        http.run()
