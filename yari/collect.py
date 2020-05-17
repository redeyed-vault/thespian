import random


def add(iterable: list, value: (bool, float, int, str), unique=False) -> list:
    """Adds a value into iterable.

    Args:
        iterable (list): Iterable to be added to.
        value (any): Value to add to iterable.
        unique (bool): Only unique values will be added if True.
    """
    if unique and value in iterable:
        return iterable

    iterable.append(value)
    iterable.sort()
    return iterable


def fuse(iterable: list, values: (list, tuple), unique=True) -> list:
    """Individually fuses values items to iterable collection.

    Args:
        iterable (list): Iterable to be fused with.
        values (list, tuple): Values to be fused with iterable.
        unique (bool): Determines if only unique values with be fused.
    """
    if not isinstance(iterable, list):
        raise TypeError("argument 'iterable' must be of type 'list'.")

    if not isinstance(values, (list, tuple)):
        raise TypeError("argument 'values' must be of type 'list' or 'tuple'.")

    if len(values) is 0:
        return iterable

    for value in values:
        add(iterable, value, unique)

    iterable.sort()
    return iterable


def pick(iterable: list) -> (bool, float, int, str):
    """Chooses random value from list then removes it.
    Args:
        iterable (list): Iterable to pick from.
    """
    if not isinstance(iterable, list):
        raise TypeError("argument 'iterable' must be of type 'list'.")

    if len(iterable) is 0:
        raise ValueError("cannot pick from an empty iterable.")

    selection = random.choice(iterable)
    iterable.remove(selection)
    return selection


def purge(iterable: list, values: (list, tuple)) -> list:
    """Individual purges values from iterable.

    Args:
        iterable (list): Iterable to remove values from.
        values (values): Collection of values to remove from iterable.
    """
    if not isinstance(iterable, list):
        raise TypeError("argument iterable must be of type 'list'.")

    if not isinstance(values, (list, tuple)):
        raise TypeError("argument 'values' must be of type 'list' or 'tuple'.")

    for value in values:
        if value in iterable:
            iterable.remove(value)
    return iterable
