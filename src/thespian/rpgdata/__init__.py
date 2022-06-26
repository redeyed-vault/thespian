from .dnd5e import dnd5e


class SourceTree:
    backgrounds: object = dnd5e["backgrounds"]
    classes: object = dnd5e["classes"]
    feats: object = dnd5e["feats"]
    metrics: object = dnd5e["metrics"]
    races: object = dnd5e["races"]
    skills: object = dnd5e["skills"]
    spell_lists: object = dnd5e["spell_lists"]
    subclasses: object = dnd5e["subclasses"]
    subraces: object = dnd5e["subraces"]
