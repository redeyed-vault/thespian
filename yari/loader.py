import os
import traceback

import yaml


class QueryNotFound(Exception):
    """Raised when a query cannot be found."""


class StructuralError(Exception):
    """Raised if the YAML layout structure is invalid."""


class HeaderInvalid(StructuralError):
    """Raised if header doesn't match file name or is otherwise invalid."""


class Query:
    """
    Handles successful query result.

    :param dict resource: The loaded YAML file contents.

    """

    def __init__(self, resource: dict) -> None:
        if not isinstance(resource, dict):
            raise TypeError("Argument 'resource' must be of type 'dict'.")
        self.resource = resource

    def find(self, *fields):
        """
        Searches the resource using the specified field(s).

        :param fields: Field index(es) to search for.

        """
        if len(fields) is 0:
            yield tuple(self.resource.keys())
        else:
            resource = self.resource
            for field in fields:
                if field in resource:
                    resource = resource[field]
                else:
                    raise QueryNotFound(f"Cannot find index '{field}' within resource.")
            yield resource


def _read(*fields, file: str) -> (dict, list):
    """
    Loads and reads from the requested file using query chain links.

    :param fields: Index(es) to query.
    :param str file: YAML file to read from (file extension is not needed).

    """

    def yopen(yaml_file: str) -> Query:
        data = os.path.join(os.path.dirname(__file__), f"sources/{yaml_file}.yml")
        if not os.path.exists(data):
            raise FileNotFoundError(f"Cannot find the resource '{yaml_file}.yml'")

        try:
            resource = yaml.full_load(open(data))[yaml_file]
            return Query(resource)
        except KeyError:
            raise HeaderInvalid(
                f"The opening key in '{yaml_file}.yml' is invalid. The first line "
                "in Yari specific YAML documents must begin with a key that "
                "matches the file name without the extension."
            )

    try:
        y = yopen(file)
        return y.find(*fields)
    except (FileNotFoundError, TypeError) as error:
        print(error)
        traceback.print_exc()
        exit()
    except HeaderInvalid as error:
        exit(error)
    except QueryNotFound:
        pass
