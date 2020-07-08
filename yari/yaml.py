import os
import yaml


class QueryNotFound(Exception):
    """Raised when a query cannot be found."""


class StructuralError(Exception):
    """Raised if the YAML layout structure is invalid."""


class HeaderInvalid(StructuralError):
    """Raised if header doesn't match file name or is otherwise invalid."""


class Query:
    """Handles successful query result."""

    def __init__(self, content: dict) -> None:
        """

        Args:
            content (dict): The loaded YAML file contents.

        """
        if not isinstance(content, dict):
            raise TypeError("stream argument must be of type 'dict'")
        else:
            self.stream = content
            self.ids = tuple(self.stream.keys())

    def fetch(self, *fields):
        """

        Args:
            fields:

        """
        if len(fields) is 0:
            return self.ids
        else:
            stream = self.stream
            for field in fields:
                if field in stream:
                    stream = stream[field]
                else:
                    raise QueryNotFound(f"Invalid index '{field}' specified.")
            return stream


def _read(*fields, file: str) -> (dict, list):
    """Loads and reads from the requested file using query chain links.

    Args:
        fields (None, tuple): Chain of values used to query YAML elements.
        file (str): YAML file to read from (file extension is not needed).

    """

    def yaml_open(yaml_file: str) -> Query:
        data = os.path.join(os.path.dirname(__file__), f"sources/{yaml_file}.yml")
        if not os.path.exists(data):
            raise FileNotFoundError(f"Cannot find the resource '{yaml_file}.yml'")
        else:
            resource = yaml.full_load(open(data))
            try:
                return Query(resource[yaml_file])
            except KeyError:
                raise HeaderInvalid(
                    f"The opening key in '{yaml_file}.yml' is invalid. The first line "
                    "in Yari specific YAML documents must begin with a key that "
                    "matches the file name without the extension."
                )

    try:
        y = yaml_open(file)
        return y.fetch(*fields)
    except (FileNotFoundError, HeaderInvalid, TypeError) as e:
        exit(e)
    except QueryNotFound:
        pass
