"""
Configuration for the LM Studio Chat Application.
"""
import json
import os
import platform
import logging # Added import
import urllib.parse # Added for URL parsing
from typing import Any # Added to resolve lint error

# --- Default Configuration ---
# LM Studio API endpoint
API_BASE_URL = "http://192.168.1.82:1234" # Store only base IP:PORT
CHAT_COMPLETIONS_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions" # Append /v1/chat/completions

# Model settings (can be adjusted as needed)

# Standardized parameter names (lowercase with underscores)
model_name = "local-model" # Or the specific model you are using in LM Studio
temperature = 0.7
max_tokens = 500
stream = False # Streaming responses can be implemented later

# System Prompt - set to None or a string
system_prompt = "You are a helpful AI assistant."
# system_prompt = None

# --- User Specific Configuration ---
# Get the appropriate user-specific configuration directory
if platform.system() == "Windows":
    APP_CONFIG_DIR = os.path.join(os.getenv("APPDATA", ""), "Retrochat")
else:
    APP_CONFIG_DIR = os.path.join(os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "Retrochat")

# Create the directory if it doesn't exist
if not os.path.exists(APP_CONFIG_DIR):
    os.makedirs(APP_CONFIG_DIR, exist_ok=True)

USER_SETTINGS_FILE = os.path.join(APP_CONFIG_DIR, "user_settings.json")


# --- Session Management ---
# Ensure sessions are stored in a 'sessions' subdirectory within the user-specific config directory
SESSIONS_DIR = os.path.join(APP_CONFIG_DIR, "sessions")  # Path to store session files
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR, exist_ok=True)

LAST_SESSION_FILE = os.path.join(APP_CONFIG_DIR, ".last_session") # Stores the ID of the last active session


# Additional model parameters (standardized)
top_p = 0.95 # Nucleus sampling: 0.1 to 1.0
presence_penalty = 0.0 # -2.0 to 2.0
frequency_penalty = 0.0 # -2.0 to 2.0
stop_sequences = [] # List of strings, e.g., ["\\nUser:", "Observation:"]

# --- Known Model Parameters ---
KNOWN_MODEL_PARAMS = {
    "model_name": str,
    "temperature": float,
    "max_tokens": int,
    "stream": bool,
    "system_prompt": (str, type(None)), # Allow None, ensure empty string becomes None
    "top_p": float,
    "presence_penalty": float,
    "frequency_penalty": float,
    "stop_sequences": list,
}

# --- Parameter Type Validation and Conversion ---
def _validate_and_convert(param_name: str, value: Any, expected_type_info: Any) -> Any:
    """
    Validates and converts a value to its expected type.
    Returns the converted value or raises ValueError/TypeError.
    """
    if param_name == "system_prompt" and value == "":
        return None # Convert empty string for system_prompt to None

    # Handle cases where expected_type_info is a single type (e.g., str, int)
    # or a tuple of types (e.g., (str, type(None)))
    if isinstance(expected_type_info, tuple): # e.g. (str, type(None))
        # Try to convert to the primary type first if not None
        if value is not None:
            primary_type = next(t for t in expected_type_info if t is not type(None))
            try:
                converted_value = primary_type(value)
                if isinstance(converted_value, primary_type): # Check successful conversion
                     return converted_value
            except (ValueError, TypeError):
                 pass # Will be caught by the isinstance check below if no type matches

        # Check if value is an instance of any of the allowed types
        if isinstance(value, expected_type_info):
            return value
        raise TypeError(f"Parameter '{param_name}' expects type {expected_type_info}, but got {type(value)} ('{value}').")

    # Single type case
    try:
        converted_value = expected_type_info(value)
        # Additional check for bool, as bool("False") is True
        if expected_type_info == bool and isinstance(value, str):
            if value.lower() in ["true", "1", "yes"]:
                return True
            elif value.lower() in ["false", "0", "no"]:
                return False
            else:
                raise ValueError(f"Cannot convert string '{value}' to boolean for parameter '{param_name}'. Use 'true' or 'false'.")
        
        # For lists, ensure elements are strings if it's stop_sequences
        if param_name == "stop_sequences" and expected_type_info == list:
            if not isinstance(value, list):
                 raise TypeError(f"Parameter '{param_name}' expects a list, but got {type(value)}.")
            if not all(isinstance(item, str) for item in value):
                raise ValueError(f"All items in '{param_name}' list must be strings.")
            return value # Already validated as list of strings or an empty list

        return converted_value
    except (ValueError, TypeError) as e:
        raise ValueError(f"Error converting value '{value}' for parameter '{param_name}' to {expected_type_info}: {e}")


def get_default_settings():
    """Returns a dictionary of the default settings (all lowercase with underscores)."""
    return {
        "api_base_url": API_BASE_URL, # Add default API base URL (http://ip:port)
        "model_name": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
        "system_prompt": system_prompt,
        "top_p": top_p,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "stop_sequences": stop_sequences.copy(),
    }

def load_user_settings() -> dict:
    """Loads user settings from the JSON file."""
    global API_BASE_URL, CHAT_COMPLETIONS_ENDPOINT
    if os.path.exists(USER_SETTINGS_FILE):
        try:
            with open(USER_SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                
                # New loading logic:
                # 1. Check for a directly set chat_completions_endpoint
                # 2. Check for api_base_url
                # 3. Fallback to defaults if specific settings are not found

                user_api_base_url = loaded_settings.get("api_base_url")
                user_chat_completions_endpoint = loaded_settings.get("chat_completions_endpoint")

                if user_chat_completions_endpoint:
                    CHAT_COMPLETIONS_ENDPOINT = user_chat_completions_endpoint
                    # If api_base_url is also in settings, use it. Otherwise, parse from full endpoint.
                    if user_api_base_url:
                        API_BASE_URL = user_api_base_url
                    else:
                        try:
                            parsed_url = urllib.parse.urlparse(CHAT_COMPLETIONS_ENDPOINT)
                            API_BASE_URL = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        except Exception as e:
                            logging.warning(f"Could not parse API_BASE_URL from CHAT_COMPLETIONS_ENDPOINT '{CHAT_COMPLETIONS_ENDPOINT}': {e}. API_BASE_URL might be stale.")
                            # API_BASE_URL will retain its previous value (default or from last successful set)
                elif user_api_base_url:
                    API_BASE_URL = user_api_base_url
                    CHAT_COMPLETIONS_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"
                # If neither is set, globals retain their default values or values from previous script run.
                
                return loaded_settings
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Error loading user settings from {USER_SETTINGS_FILE}: {e}. Using defaults.")
            return {} # Return empty if error, so defaults are used
    return {} # Return empty if file doesn't exist

def save_user_settings(settings: dict):
    """Saves user settings to the JSON file."""
    try:
        with open(USER_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except IOError as e:
        logging.error(f"Error saving user settings to {USER_SETTINGS_FILE}: {e}") # Added logging

def update_api_base_url(ip_port_str: str):
    """Updates the API_BASE_URL (e.g., http://192.168.1.82:1234) and saves it.
    This implies the chat completions path will be the default /v1/chat/completions.
    """
    global API_BASE_URL, CHAT_COMPLETIONS_ENDPOINT
    
    # Determine the new base URL value from input
    new_api_base_url_value = ""
    if not ip_port_str.startswith(("http://", "https://")):
        new_api_base_url_value = f"http://{ip_port_str}"
    else:
        new_api_base_url_value = ip_port_str

    # Load current settings from file to preserve other unrelated settings.
    # Note: load_user_settings() also updates globals based on file content,
    # but we will explicitly set globals after saving.
    current_disk_settings = load_user_settings() 

    # Prepare the settings to be saved:
    settings_to_save = current_disk_settings.copy() # Make a copy to modify

    # Update with our intended changes
    settings_to_save["api_base_url"] = new_api_base_url_value
    settings_to_save.pop("chat_completions_endpoint", None) # Remove custom endpoint to revert to default path

    save_user_settings(settings_to_save)

    # Now that settings are saved, update the globals in this module to reflect the new state.
    API_BASE_URL = new_api_base_url_value
    CHAT_COMPLETIONS_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"
    
    logging.info(f"API base URL updated to: {API_BASE_URL}")
    logging.info(f"Chat completions endpoint reset to default path: {CHAT_COMPLETIONS_ENDPOINT}")
    # Reload config to ensure globals are updated everywhere
    # from retrochat_app.core.config import load_config # Assuming this reloads based on current state
    # load_config()


def update_chat_completions_endpoint_direct(full_url: str):
    """Updates the CHAT_COMPLETIONS_ENDPOINT directly to the given full_url and saves it.
    Also attempts to parse and save the base URL from this full_url.
    """
    global API_BASE_URL, CHAT_COMPLETIONS_ENDPOINT
    
    new_full_endpoint_value = full_url
    # Attempt to parse the base URL from the new full_url
    # Default to the current global API_BASE_URL if parsing fails or is incomplete
    parsed_base_url_value = API_BASE_URL 

    try:
        parsed_url_obj = urllib.parse.urlparse(new_full_endpoint_value)
        if parsed_url_obj.scheme and parsed_url_obj.netloc:
            parsed_base_url_value = f"{parsed_url_obj.scheme}://{parsed_url_obj.netloc}"
        else:
            logging.warning(f"Could not parse a valid base URL from '{new_full_endpoint_value}'. API_BASE_URL may not be updated optimally if it wasn't already correct.")
    except Exception as e:
        logging.warning(f"Error parsing base URL from '{new_full_endpoint_value}': {e}. API_BASE_URL may not be updated optimally.")

    # Load current settings from file to preserve other unrelated settings.
    current_disk_settings = load_user_settings()

    # Prepare the settings to be saved:
    settings_to_save = current_disk_settings.copy()

    # Update with our intended changes
    settings_to_save["api_base_url"] = parsed_base_url_value
    settings_to_save["chat_completions_endpoint"] = new_full_endpoint_value

    save_user_settings(settings_to_save)

    # Now that settings are saved, update the globals in this module to reflect the new state.
    API_BASE_URL = parsed_base_url_value
    CHAT_COMPLETIONS_ENDPOINT = new_full_endpoint_value

    logging.info(f"Chat completions endpoint updated to: {CHAT_COMPLETIONS_ENDPOINT}")
    logging.info(f"API base URL (parsed or existing) set to: {API_BASE_URL}")
    # Reload config to ensure globals are updated everywhere
    # from retrochat_app.core.config import load_config # Assuming this reloads based on current state
    # load_config()

def update_model_parameter(param_name: str, value: Any) -> bool:
    """
    Updates a specific model parameter, validates its type, and saves it to user settings.
    """
    param_name_lower = param_name.lower()

    if param_name_lower not in KNOWN_MODEL_PARAMS:
        logging.error(f"Attempted to set unknown model parameter: '{param_name_lower}'")
        return False

    expected_type = KNOWN_MODEL_PARAMS[param_name_lower]

    try:
        converted_value = _validate_and_convert(param_name_lower, value, expected_type)
    except (ValueError, TypeError) as e:
        logging.error(f"Validation/conversion error for parameter '{param_name_lower}': {e}")
        print(f"Error: Could not set parameter '{param_name}'. {e}")
        return False

    current_settings = load_user_settings()  # Load existing to preserve other settings
    
    # Ensure all known model params have a default if not in current_settings
    # This is important if a new param is added to KNOWN_MODEL_PARAMS
    # and an old user_settings.json doesn't have it.
    defaults = get_default_settings()
    for key, default_val in defaults.items():
        if key in KNOWN_MODEL_PARAMS and key not in current_settings:
            current_settings[key] = default_val
            
    current_settings[param_name_lower] = converted_value
    save_user_settings(current_settings)
    
    logging.info(f"Model parameter '{param_name_lower}' updated to: {converted_value}")
    print(f"Parameter '{param_name_lower}' set to: {converted_value}")
    
    # Reload config to ensure globals are updated everywhere
    # This is crucial for the Config object in config.py to pick up changes
    # from retrochat_app.core.config import load_config # Assuming this reloads based on current state
    # load_config()
    return True

# Load initial settings, which might update API_BASE_URL
load_user_settings()
