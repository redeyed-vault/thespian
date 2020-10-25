import random
import re


def roll(string: str):
    """
    Rolls die by die string format.

    :param str string: Die string format value i.e: 2d6, 10d8, etc.

    """
    if not isinstance(string, str):
        raise TypeError("Argument 'string' must be of type 'str'.")
    else:
        if not re.search("[0-9]d[0-9]", string):
            raise ValueError("Argument 'string' has an invalid format (i.e: 4d6).")

        string = string.split("d")
        num_of_rolls = int(string[0])
        die_type = int(string[1])

        if num_of_rolls < 1:
            raise ValueError("Argument 'string' has an invalid 'num_of_rolls' value.")

        if die_type not in (4, 6, 8, 10, 12, 20, 100):
            raise ValueError("Argument 'string' has an invalid 'die_type' value.")

        for _ in range(0, num_of_rolls):
            yield random.randint(1, die_type)
