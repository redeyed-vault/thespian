from dataclasses import dataclass
import os
import traceback

import yaml


class QueryNotFound(Exception):
    """Raised when a query cannot be found."""


class MalformedError(Exception):
    """Raised if the YAML data structure is invalid."""


# TODO: Expand this class for formatting consistency checking
# Not implemented
@dataclass
class IntegrityChecker:

    check_file: str
    resource_data: dict
    # missing_keys: list = list()

    def check(self):
        self.key_table = {
            "classes": [
                "abilities",
                "background",
                "equipment",
                "features",
                "hit_die",
                "proficiency",
                "spell_slots",
                "subclasses",
            ],
            "races": ["bonus", "languages", "ratio", "size", "speed", "traits"],
            "subclasses": ["features", "magic", "proficiency"],
            "subraces": ["bonus", "languages", "parent", "ratio", "traits"],
        }

        # Requested file isn't in the key table
        if check_file not in self.key_table:
            return True

        self.required_keys = self.key_table[self.check_file]
        entry_keys = list(self.resource_data.get(self.check_file).keys())
        for key in entry_keys:
            x = self.resource_data.get(self.check_file).get(key)
            if not all(k in x for k in self.required_keys):
                return False
        return True


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


def integrity_check(check_file: str, resource_data: dict) -> bool:
    """
    Checks YAML source file integrity.

    :param str check_file:
    :param dict resource_data:

    """
    required_key_table = {
        "classes": [
            "abilities",
            "background",
            "equipment",
            "features",
            "hit_die",
            "proficiency",
            "spell_slots",
            "subclasses",
        ],
        "races": ["bonus", "languages", "ratio", "size", "speed", "traits"],
        "subclasses": ["features", "magic", "proficiency"],
        "subraces": ["bonus", "languages", "parent", "ratio", "traits"],
    }

    # Requested file isn't in the key table
    if check_file not in required_key_table:
        return True

    required_keys = required_key_table[check_file]
    entry_keys = list(resource_data.get(check_file).keys())
    for key in entry_keys:
        x = resource_data.get(check_file).get(key)
        if not all(k in x for k in required_keys):
            return False
    return True


def load(*fields, file: str):
    """
    Loads the requested YAML file and pulls requested fields.

    :param fields: Index(es) to query.
    :param str file: YAML file to read from (file extension is not needed).

    """

    def _load(file_name):
        try:
            sources_path = os.path.join(os.path.dirname(__file__), "sources/")
            yaml_file = os.path.join(sources_path, f"{file_name}.yaml")

            # File doesn't exist
            if not os.path.exists(yaml_file):
                raise FileNotFoundError(f"Cannot find the resource '{yaml_file}'.")

            with open(yaml_file) as data:
                resource = yaml.full_load(data)
                yaml_file = os.path.basename(yaml_file).replace(".yaml", "")
                if yaml_file not in resource:
                    raise MalformedError(
                        f"The opening key in '{yaml_file}' is invalid. The first line "
                        "in Yari specific YAML documents must begin with a key that "
                        "matches the file name without the extension."
                    )
                data.close()

            # TODO: Expand this formatting consistency checker
            if not integrity_check(yaml_file, resource):
                raise MalformedError(
                    f"Inconsistency formatting found in '{yaml_file}.yaml'. Please check the file and correct."
                )

            y = Query(resource[yaml_file])
            return y.find(*fields)
        except TypeError as error:
            print(error)
            traceback.print_exc()
            exit()
        except FileNotFoundError as error:
            exit(error)
        except MalformedError as error:
            exit(error)

    try:
        return [q for q in _load(file)][0]
    except QueryNotFound:
        pass
