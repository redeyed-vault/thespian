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

    def _get_rows(self, row_ids: tuple):
        for _id in row_ids:
            yield self._load(_id, file=self.source_file)

    @staticmethod
    def _load(*fields, file: str):
        """
        Loads the requested YAML file and pulls requested fields.

        :param fields: Index(es) to query.
        :param str file: YAML file to read from (file extension is not needed).

        """

        def _load_source(file_name: str):
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
            except (FileNotFoundError, MalformedError) as error:
                sys.exit(error)

        try:
            return [q for q in _load_source(file)][0]
        except QueryNotFound:
            pass

    @classmethod
    def get_columns(cls, *cols, source_file):
        """Returns row columns."""
        cls.__init__(cls, source_file)
        return cls._load(*cols, file=cls.source_file)

    @classmethod
    def get_row_ids(cls, source_file: str) -> tuple:
        """Returns row ids."""
        cls.__init__(cls, source_file)
        return cls._load(file=cls.source_file)

    def get_rows(self) -> (tuple, None):
        """Returns all rows."""
        row_ids = self.get_row_ids()
        if len(row_ids) > 0:
            return tuple(d for d in self._get_rows(row_ids))
        return None


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
