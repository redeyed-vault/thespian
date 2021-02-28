from math import ceil

from yari.builder._yaml import Load


def get_default_background(klass: str):
    """
    Returns the default background by klass.

    :param str klass: Characters chosen class.

    """
    return Load.get_columns(klass, "background", source_file="classes")


def get_is_background(background: str) -> bool:
    """
    Returns whether the background is valid.

    :param str background: Chosen background to check.

    """
    return background in PC_BACKGROUNDS


def get_is_class(klass: str) -> bool:
    """
    Returns whether the klass is valid.

    :param str klass: Character's chosen class.

    """
    return klass in PC_CLASSES


def get_is_race(race: str) -> bool:
    """
    Returns whether the race is valid.

    :param str race: Character's chosen race.

    """
    return race in PC_RACES


def get_is_subclass(subclass: str, klass: str) -> bool:
    """
    Returns whether subclass is a valid subclass of klass.

    :param str subclass: Character's chosen subclass.
    :param str klass: Character's chosen class.

    """
    return subclass in Load.get_columns(klass, "subclasses", source_file="classes")


def get_subclass_proficiency(subclass: str, category: str):
    """
    Returns subclass bonus proficiencies (if ANY).

    :param str subclass: Character subclass to get proficiencies for.
    :param str category: Proficiency category to get proficiencies for.

    """
    if category not in ("Armor", "Tools", "Weapons"):
        raise ValueError("Argument 'category' must be 'Armor', 'Tools' or 'Weapons'.")

    trait_list = Load.get_columns(subclass, source_file="subclasses")
    if trait_list.get("proficiency") is not None:
        proficiencies = trait_list.get("proficiency")
        for proficiency in proficiencies:
            if proficiency[0] == category:
                yield proficiency[1]


def get_all_languages() -> tuple:
    """Returns a tuple of ALL languages."""
    return PC_LANGUAGES


def get_all_skills() -> tuple:
    """Returns a tuple of ALL skills."""
    return PC_SKILLS


def get_background_skills(background: str):
    """
    Returns bonus skills by background (if applicable).

    :param str background: Background to return background skills for.

    """
    return Load.get_columns(background, "skills", source_file="backgrounds")


def get_language_by_class(klass: str):
    """
    Returns a tuple of class specific languages by klass, (if applicable).

    :param str klass:

    """
    return Load.get_columns(klass, "languages", source_file="classes")


def get_proficiency_bonus(level: int) -> int:
    """
    Returns a proficiency bonus value by level.

    :param int level: Level of character.

    """
    return ceil((level / 4) + 1)


def get_skills_by_subclass(subclass: str) -> tuple:
    """
    Returns a tuple of bonus skills for subclass, (if applicable).

    :param str subclass:

    """
    return Load.get_columns(subclass, "skills", source_file="subclasses")


def get_subclasses_by_class(klass: str) -> tuple:
    """
    Returns a tuple of valid subclasses for klass.

    :param str klass: Character's class.

    """
    return Load.get_columns(klass, "subclasses", source_file="classes")


def get_subraces_by_race(race: str):
    """Yields a list of valid subraces by race.
    :param str race: Race to retrieve subraces for.
    """
    for subrace in PC_SUBRACES:
        if Load.get_columns(subrace, "parent", source_file="subraces") == race:
            yield subrace


def has_extended_magic(subclass: str) -> bool:
    """
    Returns whether class subclass has spells.

    :param str subclass: Character's subclass.

    """
    if Load.get_columns(subclass, "magic", source_file="subclasses") is not None:
        return True
    return False


def has_subraces(race: str) -> bool:
    """
    Determines if race has subraces.

    :param str race: Race to determine if it has subraces.

    """
    try:
        return [s for s in get_subraces_by_race(race)][0]
    except IndexError:
        return False


def prompt(message: str, options: (list, tuple)) -> str:
    try:
        user_value = str(input(f"{message} "))
        if user_value in options:
            return user_value
        else:
            raise ValueError
    except ValueError:
        return prompt(message, options)
