import json
import os


def load_items(filename):
    """Load JSON file and return only the items list."""
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["items"]


def get_unclaimed_items(items):
    """Return only items whose status is 'unclaimed'."""
    return [item for item in items if item.get("status") == "unclaimed"]


def save_result(result, filename):
    """Save result as JSON, creating the output directory if needed."""
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)