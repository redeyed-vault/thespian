import random
import re


def roll(string: (str, int)):
    """Rolls die by die string format.

    Args:
        string (str): Die string format value i.e: 2d6, 10d8, etc.

    """
    if isinstance(string, int):
        yield string
    elif isinstance(string, str):
        if not re.search("[0-9]d[0-9]", string):
            raise ValueError("die string format invalid")
        string = string.split("d")
        num_of_rolls = int(string[0])
        if num_of_rolls < 1:
            raise ValueError("num_of_rolls must be >= 1")
        die_type = int(string[1])
        if die_type not in (4, 6, 8, 10, 12, 20, 100):
            raise ValueError("die_type value is invalid")
        for _ in range(0, num_of_rolls):
            yield random.randint(1, die_type)
