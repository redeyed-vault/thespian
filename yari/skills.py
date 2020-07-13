import random

from yari.loader import _read


class SkillGenerator:
    """Generates a random skill set by background and klass."""

    def __init__(self, background: str, klass: str, racial_skills: list) -> None:
        """
        Args:
            background (str): Character background.
            klass (str): Character's class.
            racial_skills (list): Character's skills.
        """
        background_skills = get_background_skills(background)
        class_skills = [
            skill
            for skill in self.get_skills_by_class(klass)
            if skill not in racial_skills and skill not in background_skills
        ]
        generated_skills = racial_skills + background_skills

        if klass in ("Rogue",):
            skill_allotment = 4
        elif klass in ("Bard", "Ranger"):
            skill_allotment = 3
        else:
            skill_allotment = 2
        generated_skills = generated_skills + random.sample(class_skills, skill_allotment)
        self.skills = generated_skills

    @staticmethod
    def get_skills_by_class(klass: str):
        """Returns a list of skills by klass.

        Args:
            klass (str): Class to get skill list for.
        """
        for skill in _read(file="skills"):
            if klass in _read(skill, "classes", file="skills"):
                yield skill


def get_all_skills() -> list:
    """Returns a list of ALL skills."""
    return _read(file="skills")


def get_background_skills(background: str):
    """Returns bonus skills by background (if applicable).

    Args:
        background (str): Background to return background skills for.

    """
    return _read(background, "skills", file="backgrounds")
