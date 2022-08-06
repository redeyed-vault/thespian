from enum import Enum

from .guidelines import guidelines


class _GuidelineDataLoader(Enum):
    """Class to hold character guideline data."""

    alignments: object = guidelines["alignments"]
    backgrounds: object = guidelines["backgrounds"]
    classes: object = guidelines["classes"]
    feats: object = guidelines["feats"]
    metrics: object = guidelines["metrics"]
    races: object = guidelines["races"]
    skills: object = guidelines["skills"]
    spell_lists: object = guidelines["spell_lists"]
    subclasses: object = guidelines["subclasses"]
    subraces: object = guidelines["subraces"]
