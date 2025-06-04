"""
Provider management: add, edit, delete, list, and select providers with in-editor editing.
"""
import os
import json
import subprocess
import platform
import logging

from retrochat_app.core.config_manager import APP_CONFIG_DIR

logger = logging.getLogger(__name__)

# Provider storage directory and index file
PROVIDERS_DIR = os.path.join(APP_CONFIG_DIR, "providers")
INDEX_FILE = os.path.join(PROVIDERS_DIR, "index.json")

# Ensure providers directory exists
os.makedirs(PROVIDERS_DIR, exist_ok=True)


def load_index():
    """Load the provider index (providers list and active provider)."""
    if not os.path.exists(INDEX_FILE):
        return {"providers": [], "active": None}
    try:
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse provider index at {INDEX_FILE}. Resetting index.")
        return {"providers": [], "active": None}


def save_index(index):
    """Save the provider index."""
    try:
        with open(INDEX_FILE, 'w') as f:
            json.dump(index, f, indent=4)
    except IOError as e:
        logger.error(f"Error saving provider index: {e}")


def list_providers():
    """Return a tuple (providers, active_name)."""
    index = load_index()
    return index.get("providers", []), index.get("active")


def get_provider(name):
    """Get provider config dict by name."""
    index = load_index()
    for entry in index.get("providers", []):
        if entry.get("name") == name:
            file_path = os.path.join(PROVIDERS_DIR, entry.get("file"))
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading provider config for {name}: {e}")
                return None
    return None


def get_active_provider():
    """Return the active provider config dict, or None."""
    index = load_index()
    active = index.get("active")
    if not active:
        return None
    return get_provider(active)


def _sanitize_filename(name: str) -> str:
    """Generate a safe filename from provider name."""
    safe = name.strip().lower().replace(' ', '_')
    # Remove unsafe characters
    safe = ''.join(c for c in safe if c.isalnum() or c in ('_', '-'))
    if not safe:
        safe = 'provider'
    return safe


def add_provider(name: str, type: str, api_base_url: str,
                 chat_completions_endpoint: str = None,
                 params: dict = None,
                 message_format: str = None,
                 response_format: str = None,
                 headers: dict = None):
    """Add a new provider and open config in editor."""
    index = load_index()
    # Prevent duplicate names
    for entry in index.get("providers", []):
        if entry.get("name") == name:
            logger.error(f"Provider '{name}' already exists.")
            return False, None
    # Determine filename
    base = _sanitize_filename(name)
    filename = f"{base}.json"
    file_path = os.path.join(PROVIDERS_DIR, filename)

    # Build default config
    # Determine default chat completions endpoint
    endpoint = chat_completions_endpoint
    if not endpoint:
        api_base_trimmed = api_base_url.rstrip('/')
        if api_base_trimmed.endswith('/v1'):
            endpoint_base = api_base_trimmed
        else:
            endpoint_base = f"{api_base_trimmed}/v1"
        endpoint = f"{endpoint_base}/chat/completions"

    cfg = {
        "name": name,
        "type": type,
        "api_base_url": api_base_url,
        "chat_completions_endpoint": endpoint,
        "params": params or {},
        "message_format": message_format or "",
        "response_format": response_format or "",
        "headers": headers or {}
    }
    # Write config file
    try:
        with open(file_path, 'w') as f:
            json.dump(cfg, f, indent=4)
    except IOError as e:
        logger.error(f"Error writing provider config file: {e}")
        return False, None

    # Update index
    index.setdefault("providers", []).append({"name": name, "file": filename})
    save_index(index)

    # Launch editor
    _launch_editor(file_path)
    # Validate config after editing
    try:
        with open(file_path, 'r') as f:
            edited = json.load(f)
        # Basic validation
        required = ["name", "type", "api_base_url", "chat_completions_endpoint"]
        for r in required:
            if r not in edited:
                logger.error(f"Edited config missing required key: {r}")
                return False, file_path
        if "headers" in edited and not isinstance(edited["headers"], dict):
            logger.error("Edited config 'headers' must be a dictionary if present")
            return False, file_path
    except Exception as e:
        logger.error(f"Error validating edited config: {e}")
        return False, file_path

    return True, file_path


def edit_provider(name: str):
    """Open an existing provider config in editor and validate."""
    index = load_index()
    for entry in index.get("providers", []):
        if entry.get("name") == name:
            file_path = os.path.join(PROVIDERS_DIR, entry.get("file"))
            if os.path.exists(file_path):
                _launch_editor(file_path)
                # Validate
                try:
                    with open(file_path, 'r') as f:
                        edited = json.load(f)
                    required = ["name", "type", "api_base_url", "chat_completions_endpoint"]
                    for r in required:
                        if r not in edited:
                            logger.error(f"Edited config missing key: {r}")
                            return False
                    if "headers" in edited and not isinstance(edited["headers"], dict):
                        logger.error("Edited config 'headers' must be a dictionary if present")
                        return False
                    return True
                except Exception as e:
                    logger.error(f"Error validating config after edit: {e}")
                    return False
    logger.error(f"Provider '{name}' not found.")
    return False


def delete_provider(name: str):
    """Delete a provider and its config file."""
    index = load_index()
    new_list = []
    found = False
    for entry in index.get("providers", []):
        if entry.get("name") == name:
            # Remove file
            file_path = os.path.join(PROVIDERS_DIR, entry.get("file"))
            try:
                if os.path.exists(file_path): os.remove(file_path)
            except OSError as e:
                logger.error(f"Error deleting provider file: {e}")
            found = True
        else:
            new_list.append(entry)
    if not found:
        logger.error(f"Provider '{name}' not found.")
        return False
    index["providers"] = new_list
    # If deleting active, unset
    if index.get("active") == name:
        index["active"] = None
    save_index(index)
    return True


def select_provider(name: str):
    """Select a provider as active."""
    index = load_index()
    for entry in index.get("providers", []):
        if entry.get("name") == name:
            index["active"] = name
            save_index(index)
            return True
    logger.error(f"Provider '{name}' not found.")
    return False


def _launch_editor(file_path: str):
    """Launch the system default editor to edit the provider config."""
    system = platform.system()
    try:
        if system == 'Windows':
            subprocess.run(["notepad", file_path], check=True)
        elif system == 'Darwin':
            subprocess.run(["open", "-e", file_path], check=True)
        else:
            editor = os.getenv('EDITOR', 'nano')
            subprocess.run([editor, file_path], check=True)
    except Exception as e:
        logger.error(f"Error launching editor for {file_path}: {e}")
