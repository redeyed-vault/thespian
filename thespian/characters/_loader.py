from enum import Enum

from .rulesets import rules


class RulesLoader(Enum):
    """Class to handle the retrieval and storage of rule data."""

    alignments: object = rules["alignments"]
    backgrounds: object = rules["backgrounds"]
    classes: object = rules["classes"]
    feats: object = rules["feats"]
    metrics: object = rules["metrics"]
    races: object = rules["races"]
    skills: object = rules["skills"]
    spell_lists: object = rules["spell_lists"]
    subclasses: object = rules["subclasses"]
    subraces: object = rules["subraces"]
