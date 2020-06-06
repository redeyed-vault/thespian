import os
import yaml


class HeaderNotFound(Exception):
    """Raised if YAML file doesn't have a matching main data node."""


class NodeNotFound(HeaderNotFound):
    """Raised when the requested YAML node cannot be found."""


class QueryNotFound(Exception):
    """Raised when a query cannot be found."""


class ReaderResult:
    """Handles successful query result."""

    def __init__(self, stream: dict, node: str) -> None:
        """

        Args:
            stream (dict): YAML file stream resource.
            node (str): Data node (index) to initialize.

        """
        if not isinstance(stream, dict):
            raise TypeError("stream argument must be of type 'dict'")
        elif node not in stream:
            raise NodeNotFound(f"invalid data node index '{node}'")
        else:
            self.stream = stream.get(node)

    def fetch(self, query_links: (None, tuple)):
        """

        Args:
            query_links:

        """
        if not isinstance(query_links, tuple):
            if query_links is None:
                yield tuple(self.stream.keys())
            else:
                raise TypeError("links argument must be of type 'tuple'")
        elif len(query_links) is 0:
            raise ValueError("links argument is empty")
        else:
            for query in query_links:
                if query in self.stream:
                    self.stream = self.stream[query]
                    yield self.stream
                else:
                    raise QueryNotFound(f"specified query unsuccessful '{query}'")


def _load(file: str) -> ReaderResult:
    """Loads ReaderResult object on success or raises exception on error.

    Args:
        file (str): YAML file to read from (file extension is not needed).

    """
    data = os.path.join(os.path.dirname(__file__), f"sources/{file}.yml")
    if not os.path.exists(data):
        raise FileNotFoundError(f"cannot load YAML file '{data}'")

    source = yaml.load(open(data), Loader=yaml.FullLoader)
    if file not in source:
        raise HeaderNotFound(f"YAML header missing for '{file}'")
    else:
        return ReaderResult(source, file)


def reader(file: str, links=None) -> (dict, list):
    """Loads and reads from the requested file using query chain links.

    Args:
        file (str): YAML file to read from (file extension is not needed).
        links (None, tuple): Chain of values used to query YAML elements.

    """
    try:
        rd = _load(file)
        holder = [r for r in rd.fetch(links)]
        return holder[0]
    except (FileNotFoundError, NodeNotFound, TypeError,) as error:
        exit(error)
    except QueryNotFound:
        pass
