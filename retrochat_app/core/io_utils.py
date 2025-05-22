'''
Utility functions for file input/output operations with error handling.
'''
import json
import logging
import os

logger = logging.getLogger(__name__)

def read_json_file(filepath: str) -> dict | None:
    """
    Reads data from a JSON file.

    Args:
        filepath: The path to the JSON file.

    Returns:
        A dictionary containing the loaded JSON data, or None if an error occurs.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logger.error(f"Error: File not found at {filepath}")
        return None
    except IOError as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from file {filepath}: {e}")
        return None

def write_json_file(filepath: str, data: dict) -> bool:
    """
    Writes data to a JSON file.

    Args:
        filepath: The path to the JSON file.
        data: The dictionary data to write to the file.

    Returns:
        True if the write operation was successful, False otherwise.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except IOError as e:
        logger.error(f"Error writing to file {filepath}: {e}")
        return False
    except TypeError as e:
        logger.error(f"Error serializing data to JSON for file {filepath}: {e}")
        return False
