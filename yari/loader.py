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
        if len(fields) == 0:
            yield tuple(self.resource.keys())
        else:
            resource = self.resource
            for field in fields:
                if field in resource:
                    resource = resource[field]
                else:
                    raise QueryNotFound(f"Cannot find index '{field}' within resource.")
            yield resource


def load(*fields, file: str):
    """
    Loads the requested YAML file and pulls requested fields.

    :param fields: Index(es) to query.
    :param str file: YAML file to read from (file extension is not needed).

    """

    def _load(file_name):
        try:
            sources_path = os.path.join(os.path.dirname(__file__), "sources/")
            file_name = os.path.join(sources_path, f"{file_name}.yml")
            if not os.path.exists(file_name):
                raise FileNotFoundError(f"Cannot find the resource '{file_name}'.")
            data = open(file_name)
            resource = yaml.full_load(data)
            file_name = os.path.basename(file_name).replace(".yml", "")
            if file_name not in resource:
                raise HeaderInvalid(
                    f"The opening key in '{file_name}' is invalid. The first line "
                    "in Yari specific YAML documents must begin with a key that "
                    "matches the file name without the extension."
                )
            y = Query(resource[file_name])
            return y.find(*fields)
        except (FileNotFoundError, TypeError) as error:
            print(error)
            traceback.print_exc()
            exit()
        except HeaderInvalid as error:
            exit(error)

    try:
        return [q for q in _load(file)][0]
    except QueryNotFound:
        pass
