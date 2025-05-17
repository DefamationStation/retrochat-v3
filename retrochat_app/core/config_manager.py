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
MODEL_NAME = "local-model" # Or the specific model you are using in LM Studio
TEMPERATURE = 0.7
MAX_TOKENS = 500
STREAM = False # Streaming responses can be implemented later

# System Prompt - set to None or a string
SYSTEM_PROMPT = "You are a helpful AI assistant."
# SYSTEM_PROMPT = None 

# --- User Specific Configuration ---
CONFIG_DIR = os.path.dirname(__file__)
USER_SETTINGS_FILE = os.path.join(CONFIG_DIR, "user_settings.json")

# --- Session Management ---
SESSIONS_DIR = os.path.join(os.path.dirname(CONFIG_DIR), "sessions") # Path to store session files
LAST_SESSION_FILE = os.path.join(CONFIG_DIR, ".last_session") # Stores the ID of the last active session

# Additional model parameters (refer to LM Studio documentation for your specific model)
TOP_P = 0.95 # Nucleus sampling: 0.1 to 1.0
PRESENCE_PENALTY = 0.0 # -2.0 to 2.0
FREQUENCY_PENALTY = 0.0 # -2.0 to 2.0
STOP_SEQUENCES = [] # List of strings, e.g., ["\\nUser:", "Observation:"]

def get_default_settings():
    """Returns a dictionary of the default settings."""
    return {
        "MODEL_NAME": MODEL_NAME,
        "TEMPERATURE": TEMPERATURE,
        "MAX_TOKENS": MAX_TOKENS,
        "STREAM": STREAM,
        "SYSTEM_PROMPT": SYSTEM_PROMPT,
        "TOP_P": TOP_P,
        "PRESENCE_PENALTY": PRESENCE_PENALTY,
        "FREQUENCY_PENALTY": FREQUENCY_PENALTY,
        "STOP_SEQUENCES": STOP_SEQUENCES.copy(),
    }

def load_user_settings() -> dict:
    """Loads user settings from the JSON file."""
    if os.path.exists(USER_SETTINGS_FILE):
        try:
            with open(USER_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading user settings from {USER_SETTINGS_FILE}: {e}. Using defaults.")
            return {} # Return empty if error, so defaults are used
    return {} # Return empty if file doesn't exist

def save_user_settings(settings: dict):
    """Saves user settings to the JSON file."""
    try:
        with open(USER_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except IOError as e:
        print(f"Error saving user settings to {USER_SETTINGS_FILE}: {e}")
