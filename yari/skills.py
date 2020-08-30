from yari.loader import load


def get_all_skills() -> list:
    """Returns a list of ALL skills."""
    return [s for s in load(file="skills")][0]


def get_background_skills(background: str):
    """Returns bonus skills by background (if applicable).

    Args:
        background (str): Background to return background skills for.

    """
    return [s for s in load(background, "skills", file="backgrounds")][0]
