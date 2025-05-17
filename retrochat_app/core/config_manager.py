"""
Configuration for the LM Studio Chat Application.
"""

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

# Additional model parameters (refer to LM Studio documentation for your specific model)
TOP_P = 0.95 # Nucleus sampling: 0.1 to 1.0
PRESENCE_PENALTY = 0.0 # -2.0 to 2.0
FREQUENCY_PENALTY = 0.0 # -2.0 to 2.0
STOP_SEQUENCES = [] # List of strings, e.g., ["\nUser:", "Observation:"]
