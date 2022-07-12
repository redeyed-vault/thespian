from . import Guidelines


def get_base_height(race: str) -> str | None:
    """Returns base height values by race."""
    try:
        return Guidelines.metrics[race]["height"]
    except (AttributeError, KeyError, TypeError):
        return None


def get_base_weight(race: str) -> str | None:
    """Returns base weight values by race."""
    try:
        return Guidelines.metrics[race]["weight"]
    except (AttributeError, KeyError, TypeError):
        return None


def get_dominant_sex(race: str) -> str | None:
    """Returns the physically larger gender by race."""
    try:
        return Guidelines.metrics[race]["dominant"]
    except AttributeError:
        return None


def get_default_background(klass: str) -> str:
    """Returns default background by class."""
    return Guidelines.classes[klass]["background"]


def get_entry_background(background: str) -> dict:
    """Returns config entry for background."""
    return Guidelines.backgrounds[background]


def get_entry_class(klass: str) -> dict:
    """Returns config entry for class."""
    return Guidelines.classes[klass]


def get_entry_race(race: str) -> dict:
    """Returns config entry for race."""
    return Guidelines.races[race]


def get_entry_subclass(subclass: str) -> dict:
    """Returns config entry for subclass."""
    return Guidelines.subclasses[subclass]


def get_entry_subrace(subrace: str) -> dict:
    """Returns config entry for subrace"""
    return Guidelines.subraces[subrace]


def get_feat_perks(feat_name: str) -> dict:
    """Returns perks by feat."""
    return Guidelines.feats[feat_name]["perk"]


def get_feat_proficiencies(feat: str, prof_type: str) -> list:
    """Returns bonus proficiencies by feat and proficiency type."""
    return Guidelines.feats[feat]["perk"][prof_type]


def get_feat_requirements(feat_name: str) -> dict:
    """Returns requirements by feat."""
    return Guidelines.feats[feat_name]["required"]


def get_feats_list() -> tuple:
    """Returns a tuple of all feats."""
    return tuple(Guidelines.feats.keys())


def get_metrics_by_race(race: str) -> str | None:
    """Returns metric data by race."""
    return Guidelines.metrics.get(race)


def get_pc_alignments() -> tuple:
    """Returns a tuple of all player character alignments."""
    return tuple(Guidelines.alignments.keys())


def get_pc_backgrounds() -> tuple:
    """Returns a tuple of all player character backgrounds."""
    return tuple(Guidelines.backgrounds.keys())


def get_pc_classes() -> tuple:
    """Returns a tuple of all player character classes."""
    return tuple(Guidelines.classes.keys())


def get_pc_races() -> tuple:
    """Returns a tuple of all player character races."""
    return tuple(Guidelines.races.keys())


def get_pc_subclasses(klass: str = None) -> tuple:
    """Returns a set of all player character subclasses."""
    try:
        return set(Guidelines.classes[klass]["subclass"])
    except KeyError:
        return set(Guidelines.subclasses.keys())


def get_pc_subraces(race: str = None) -> dict | None:
    """Returns a set of all player character subraces."""
    try:
        return set(Guidelines.races[race]["subrace"])
    except (AttributeError, KeyError):
        return set(Guidelines.subraces.keys())


def get_skill_ability(skill_name: str) -> str | None:
    """Returns a skill's associated ability."""
    try:
        return Guidelines.skills[skill_name]["associated_ability"]
    except AttributeError:
        return None


def get_skill_list() -> tuple:
    """Returns a tuple of all player character skills."""
    return tuple(Guidelines.skills.keys())
