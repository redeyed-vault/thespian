from yari.loader import _read


def get_all_skills() -> list:
    """Returns a list of ALL skills."""
    return _read(file="skills")


def get_background_skills(background: str):
    """Returns bonus skills by background (if applicable).

    Args:
        background (str): Background to return background skills for.

    """
    return _read(background, "skills", file="backgrounds")
