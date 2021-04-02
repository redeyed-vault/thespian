from dataclasses import dataclass
import os
from typing import Type

import yaml

from yari.errors import Error


class QueryNotFound(Exception):
    """Raised when a query cannot be found."""


class Load:
    @staticmethod
    def _load_source(*fields, file: Type[str], use_local: Type[bool] = True):
        """
        Loads the requested YAML source file and pulls requested fields.

        :param fields:
        :param str file:
        :param bool use_local:

        """
        # Use source file from local source directory
        # Or attempt to use the user specified source
        source_dir = os.path.dirname(__file__)
        if use_local:
            fpath = os.path.join(os.path.join(source_dir, "sources/"), f"{file}.yaml")
        else:
            fpath = f"{file}.yaml"

        # File 'fpath' cannot be found
        if not os.path.exists(fpath):
            raise Error(f"Cannot find the requested source file '{fpath}'.")

        # Attempt to extract the requested data
        with open(fpath) as data:
            resource = yaml.full_load(data)
            if file not in resource:
                raise Error(
                    f"The opening key in '{file}' is invalid. The first line "
                    "in Yari specific YAML documents must begin with a key that "
                    "matches the file name without the extension."
                )
            data.close()

            # Create the Query object
            qo = Query(resource.get(file))
            try:
                return [q for q in qo.fetch(*fields)][0]
            except QueryNotFound:
                return None

    @classmethod
    def get_columns(cls, *cols, source_file: str, use_local: bool = True):
        """Returns row columns."""
        return cls._load_source(*cols, file=source_file, use_local=use_local)

    @classmethod
    def get_row_ids(cls, source_file: str, use_local: bool = True) -> tuple:
        """Returns row ids."""
        return cls._load_source(file=source_file, use_local=use_local)


@dataclass
class Query:

    resource: dict

    def fetch(self, *fields):
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
