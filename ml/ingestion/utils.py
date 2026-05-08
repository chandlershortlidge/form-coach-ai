
import json
from typing import Any


def write_json(filepath_out: str, data: Any) -> None:
    """Write a Python object to disk as JSON.

    Args:
        filepath_out: Destination file path, including `.json`.
        data: JSON-serializable object to persist.
    """
    with open(filepath_out, "w") as f:
        json.dump(data, f)


def read_json(filename: str) -> Any:
    """Load JSON data from a file path.

    Args:
        filename: Path to a JSON file on disk.

    Returns:
        Parsed Python object (commonly a dict).
    """
    with open(filename, "r") as f:
        data = json.load(f)
    return data
