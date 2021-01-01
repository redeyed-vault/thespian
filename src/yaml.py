from dataclasses import dataclass
import os
import sys
import traceback

import yaml


class QueryNotFound(Exception):
    """Raised when a query cannot be found."""


class MalformedError(Exception):
    """Raised if the YAML data structure is invalid."""


@dataclass
class Load:

    source_file: str
    _data: list = None

    def get_row_column(self, *cols):
        """Returns row columns."""
        self._data = load(*cols, file=self.source_file)
        return self._data

    def get_row_ids(self):
        """Returns row ids."""
        self._data = load(file=self.source_file)
        return self._data


@dataclass
class Query:

    resource: dict

    def find(self, *fields):
        """
        Searches the resource using the specified field(s).

        :param fields: Field index(es) to search for.

        """
        if not isinstance(self.resource, dict):
            raise TypeError("Argument 'resource' must be of type 'dict'.")

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
            source_path_dir = os.path.join(os.path.dirname(__file__), "sources/")
            yaml_file_path = os.path.join(source_path_dir, f"{file_name}.yaml")

            # File doesn't exist
            if not os.path.exists(yaml_file_path):
                raise FileNotFoundError(f"Missing source file '{yaml_file_path}'.")

            # Extract the file, sans YAML extension
            base_file_name = os.path.basename(yaml_file_path).replace(".yaml", "")

            # Attempt to extract the requested data
            with open(yaml_file_path) as data:
                resource = yaml.full_load(data)
                if base_file_name not in resource:
                    raise MalformedError(
                        f"The opening key in '{base_file_name}' is invalid. The first line "
                        "in Yari specific YAML documents must begin with a key that "
                        "matches the file name without the extension."
                    )
                data.close()

            # Create then query the Query object
            y = Query(resource[base_file_name])
            return y.find(*fields)
        except TypeError as error:
            print(error)
            traceback.print_exc()
            sys.exit()
        except FileNotFoundError as error:
            sys.exit(error)
        except MalformedError as error:
            sys.exit(error)

    try:
        return [q for q in _load(file)][0]
    except QueryNotFound:
        pass
