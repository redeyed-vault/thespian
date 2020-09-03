from yari.loader import load


def get_all_skills() -> list:
    """Returns a list of ALL skills."""
    return load(file="skills")


def get_background_skills(background: str):
    """
    Returns bonus skills by background (if applicable).

    :param str background: Background to return background skills for.

    """
    return load(background, "skills", file="backgrounds")
