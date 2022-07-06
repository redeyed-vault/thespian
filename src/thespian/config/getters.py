from . import GuidelineSettings


def get_default_background(klass: str) -> str:
    """Returns default background by class."""
    return GuidelineSettings.classes[klass]["background"]


def get_entry_background(background: str) -> dict:
    """Returns config entry for background."""
    return GuidelineSettings.backgrounds[background]


def get_entry_class(klass: str) -> dict:
    """Returns config entry for class."""
    return GuidelineSettings.classes[klass]
    

def get_entry_race(race: str) -> dict:
    """Returns config entry for race."""
    return GuidelineSettings.races[race]


def get_entry_subclass(subclass: str) -> dict:
    """Returns config entry for subclass."""
    return GuidelineSettings.subclasses[subclass]


def get_entry_subrace(subrace: str) -> dict:
    """Returns config entry for subrace"""
    return GuidelineSettings.subraces[subrace]


def get_pc_backgrounds() -> tuple:
    """Returns a tuple of all player character backgrounds."""
    return tuple(GuidelineSettings.backgrounds.keys())


def get_pc_classes() -> tuple:
    """Returns a tuple of all player character classes."""
    return tuple(GuidelineSettings.classes.keys())


def get_pc_races() -> tuple:
    """Returns a tuple of all player character races."""
    return tuple(GuidelineSettings.races.keys())


def get_pc_subclasses(klass: str) -> tuple:
    """Returns a set of all player character subclasses."""
    return set(GuidelineSettings.classes[klass]["subclass"])


def get_pc_subraces(race: str) -> dict | None:
    """Returns a set of all player character subraces."""
    try:
        return set(GuidelineSettings.races[race]["subrace"])
    except AttributeError:
        return None


def get_skill_ability(skill_name: str) -> str | None:
    """Returns a skill's associated ability."""
    try:
        return GuidelineSettings.skills[skill_name]["associated_ability"]
    except AttributeError:
        return None


def get_skill_list() -> tuple:
    """Returns a tuple of all player character skills."""
    return tuple(GuidelineSettings.skills.keys())
