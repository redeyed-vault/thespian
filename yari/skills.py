import random

from yari.collect import fuse, purge
from yari.reader import reader


class SkillGenerator:
    """Generates a random skill set by background and klass."""

    def __init__(self, background: str, klass: str, bonus_racial_skills: list) -> None:
        """
        Args:
            background (str): Character background.
            klass (str): Character's class.
            bonus_racial_skills (list): Character's skills.
        """
        class_skills = self.get_skills_by_class(klass)
        generated_skills = list()

        # Remove bonus racial skills from class skills.
        if len(bonus_racial_skills) is not 0:
            purge(class_skills, bonus_racial_skills)
            fuse(generated_skills, bonus_racial_skills)

        # Remove bonus background skills from class skills.
        background_skills = reader("backgrounds", (background,)).get("skills")
        if len(background_skills) is not 0:
            purge(class_skills, background_skills)
            fuse(generated_skills, background_skills)

        if klass in ("Rogue",):
            skill_allotment = 4
        elif klass in ("Bard", "Ranger"):
            skill_allotment = 3
        else:
            skill_allotment = 2
        fuse(generated_skills, random.sample(class_skills, skill_allotment))
        self.skills = generated_skills

    @staticmethod
    def get_skills_by_class(klass):
        """Returns a list of skills by klass.

        Args:
            klass (str): Class to get skill list for.
        """
        skills = list()
        for skill in reader("skills"):
            if klass in reader("skills", (skill,)).get("classes"):
                skills.append(skill)
        return skills


def get_all_skills() -> list:
    """Returns a list of ALL valid skills."""
    return reader("skills")
