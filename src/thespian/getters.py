from sourcetree import SourceTree


def get_default_background(klass):
    """Returns default background by class."""
    return SourceTree.classes[klass]["background"]


def get_pc_backgrounds():
    """Returns a tuple of all player character backgrounds."""
    return tuple(SourceTree.backgrounds.keys())


def get_pc_classes():
    """Returns a tuple of all player character classes."""
    return tuple(SourceTree.classes.keys())


def get_pc_races():
    """Returns a tuple of all player character races."""
    return tuple(SourceTree.races.keys())


def get_pc_subclasses(klass):
    """Returns a set of all player character subclasses."""
    return set(SourceTree.classes[klass]["subclass"])


def get_pc_subraces(race):
    """Returns a set of all player character subraces."""
    try:
        return set(SourceTree.races[race]["subrace"])
    except AttributeError:
        return None


def get_skill_ability(skill_name):
    """Returns a skill's associated ability."""
    try:
        return SourceTree.skills[skill_name]["associated_ability"]
    except AttributeError:
        return None


def get_skill_list():
    """Returns a tuple of all player character skills."""
    return tuple(SourceTree.skills.keys())