"""
Configuration for the LM Studio Chat Application.
"""
import json
import os

# --- Default Configuration ---
# LM Studio API endpoint
API_BASE_URL = "http://192.168.1.82:1234/v1"
CHAT_COMPLETIONS_ENDPOINT = f"{API_BASE_URL}/chat/completions"

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
CONFIG_DIR = os.path.dirname(__file__)
USER_SETTINGS_FILE = os.path.join(CONFIG_DIR, "user_settings.json")


# --- Session Management ---
# Ensure sessions are stored in a 'sessions' subdirectory next to the config directory (not above it)
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")  # Path to store session files
LAST_SESSION_FILE = os.path.join(CONFIG_DIR, ".last_session") # Stores the ID of the last active session


# Additional model parameters (standardized)
top_p = 0.95 # Nucleus sampling: 0.1 to 1.0
presence_penalty = 0.0 # -2.0 to 2.0
frequency_penalty = 0.0 # -2.0 to 2.0
stop_sequences = [] # List of strings, e.g., ["\nUser:", "Observation:"]

def get_default_settings():
    """Returns a dictionary of the default settings (all lowercase with underscores)."""
    return {
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
    if os.path.exists(USER_SETTINGS_FILE):
        try:
            with open(USER_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            from retrochat_app.ui.display_handler import log_error, Console
            log_error(Console(), f"Error loading user settings from {USER_SETTINGS_FILE}: {e}. Using defaults.")
            return {} # Return empty if error, so defaults are used
    return {} # Return empty if file doesn't exist

def save_user_settings(settings: dict):
    """Saves user settings to the JSON file."""
    try:
        with open(USER_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except IOError as e:
        from retrochat_app.ui.display_handler import log_error, Console
        log_error(Console(), f"Error saving user settings to {USER_SETTINGS_FILE}: {e}")
