from .dnd5e import dnd5e_sources


class SourceTree:
    backgrounds: object = dnd5e_sources["backgrounds"]
    classes: object = dnd5e_sources["classes"]
    feats: object = dnd5e_sources["feats"]
    metrics: object = dnd5e_sources["metrics"]
    races: object = dnd5e_sources["races"]
    skills: object = dnd5e_sources["skills"]
    subclasses: object = dnd5e_sources["subclasses"]
    subraces: object = dnd5e_sources["subraces"]
