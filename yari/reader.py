import os
import yaml


class NodeNotFound(Exception):
    """Raised when YAML node block "table" cannot be found."""


class QueryNotFound(Exception):
    """Raised when a query cannot be found."""


class ReaderQueryResult:
    """Handles successful query result."""

    def __init__(self, data_source: dict, data_table: str) -> None:
        self.data_source = data_source.get(data_table)

    def fetch(self, query_values: (None, tuple)):
        # Empty query_values parameter specified.
        if (
            query_values is None
            or isinstance(query_values, tuple)
            and len(query_values) is 0
        ):
            return self.data_source

        if query_values is not None and not isinstance(query_values, tuple):
            raise TypeError("error: query_values argument must be type 'tuple'")

        # Check for the query_values.
        for query in query_values:
            if query in self.data_source:
                self.data_source = self.data_source[query]
            else:
                raise QueryNotFound(f"specified query unsuccessful '{query}'")
        return self.data_source


def _load(data_file: str) -> ReaderQueryResult:
    """Loads ReaderQueryResult object on success or raises exception on error.

    Args:
        data_file (str): YAML file to read from (file extension is not needed).

    """
    data = os.path.join(os.path.dirname(__file__), f"sources/{data_file}.yml")
    if not os.path.exists(data):
        raise FileNotFoundError(f"cannot load YAML file from '{data}'")

    data_source = yaml.load(open(data), Loader=yaml.FullLoader)
    if data_file not in data_source:
        raise NodeNotFound(f"invalid table specified '{data_file}'")
    else:
        return ReaderQueryResult(data_source, data_file)


def reader(data_file: str, query_values=None) -> (dict, list):
    """Loads and reads from the requested data_file using query_values.

    Args:
        data_file (str): YAML file to read from (file extension is not needed).
        query_values (None, tuple): Chain of values used to query YAML elements.

    """
    try:
        rd = _load(data_file)
        return rd.fetch(query_values)
    except (FileNotFoundError, NodeNotFound, TypeError,) as error:
        exit(error)
    except QueryNotFound:
        pass
