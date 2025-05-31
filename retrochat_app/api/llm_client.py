"""
Handles communication with the LM Studio API.
"""
import requests
import json
from typing import Optional, List, Dict, Any
# Adjusted import path for config
from retrochat_app.core.config_manager import (
    CHAT_COMPLETIONS_ENDPOINT, # Keep existing imports
    API_BASE_URL, # Add API_BASE_URL import
    load_user_settings, save_user_settings, get_default_settings # Add new functions
)

class LLMClient:
    """
    A client for interacting with the LM Studio API.
    """
    # Mapping between internal attribute names and user settings keys (all lowercase with underscores)
    PARAM_KEY_MAP = {
        "model": "model_name",
        "temperature": "temperature",
        "max_tokens": "max_tokens",
        "stream": "stream",
        "system_prompt": "system_prompt",
        "top_p": "top_p",
        "presence_penalty": "presence_penalty",
        "frequency_penalty": "frequency_penalty",
        "stop_sequences": "stop_sequences"
    }

    def __init__(self):
        self.endpoint = CHAT_COMPLETIONS_ENDPOINT
        self.default_params = get_default_settings()
        user_settings = load_user_settings()

        # Explicitly define all attributes with default values first
        self.model = self.default_params["model_name"]
        self.temperature = self.default_params["temperature"]
        self.max_tokens = self.default_params["max_tokens"]
        self.stream = self.default_params["stream"]
        self.system_prompt = self.default_params["system_prompt"]
        self.top_p = self.default_params["top_p"]
        self.presence_penalty = self.default_params["presence_penalty"]
        self.frequency_penalty = self.default_params["frequency_penalty"]
        self.stop_sequences = self.default_params["stop_sequences"].copy()

        # Now override with user settings using the mapping
        for attr, key in self.PARAM_KEY_MAP.items():
            if key in user_settings:
                val = user_settings[key]
                if attr == "stop_sequences":
                    # Ensure stop_sequences is a list, making a copy or converting as necessary.
                    # If user_settings provides a list, it's copied.
                    # If it's a tuple or other iterable, it's converted to a list.
                    # If it's None or an empty string, or other falsy value, it becomes an empty list.
                    # If it's a non-list, truthy value (e.g. a string "stop"), it's converted to list of chars (e.g. ['s','t','o','p']).
                    val = val.copy() if isinstance(val, list) else list(val) if val else []
                setattr(self, attr, val)

    def _get_current_params_payload(self) -> Dict[str, Any]:
        """Helper to get payload-ready parameters, excluding None values for stop."""
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }
        if self.stop_sequences:
            payload["stop"] = self.stop_sequences
        return payload

    def update_endpoint(self):
        """Updates the endpoint from the global config."""
        # Need to import CHAT_COMPLETIONS_ENDPOINT from config_manager again, 
        # or ensure it's passed or accessible if it can change at runtime.
        # For simplicity, assuming config_manager.CHAT_COMPLETIONS_ENDPOINT is updated globally.
        from retrochat_app.core.config_manager import CHAT_COMPLETIONS_ENDPOINT as current_chat_endpoint
        self.endpoint = current_chat_endpoint

    def send_chat_message_full_history(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Sends a chat request with the complete message history (non-streaming)."""
        if not messages:
            print("Error: Message list cannot be empty.")
            return None

        payload = self._get_current_params_payload()
        payload["messages"] = messages # Use the provided full history
        payload["stream"] = False # Ensure stream is False for this method

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(self.endpoint, headers=headers, data=json.dumps(payload), stream=False)
            response.raise_for_status()
            response_data = response.json()
            
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                # Check if 'message' key exists and has 'content'
                if "message" in response_data["choices"][0] and "content" in response_data["choices"][0]["message"]:
                    return response_data["choices"][0]["message"]["content"]
                # Fallback for models that might structure response differently, e.g. with 'delta'
                elif "delta" in response_data["choices"][0] and "content" in response_data["choices"][0]["delta"]:
                    return response_data["choices"][0]["delta"]["content"]
            return None  # Or handle as an error/empty response appropriately
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error during LLM communication: {e}")
            return None
        except json.JSONDecodeError:
            print(f"[ERROR] Failed to decode JSON response: {response.text}")
            return None

    def stream_chat_message(self, messages: List[Dict[str, Any]]):
        """Sends a chat request and streams the response."""
        if not messages:
            print("Error: Message list cannot be empty.")
            yield "" # Or raise an error
            return

        payload = self._get_current_params_payload()
        payload["messages"] = messages
        payload["stream"] = True # Ensure stream is True for this method

        headers = {"Content-Type": "application/json"}

        try:
            with requests.post(self.endpoint, headers=headers, data=json.dumps(payload), stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            json_content = decoded_line[len("data: "):]
                            if json_content.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(json_content)
                                if data.get("choices") and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                print(f"[ERROR] Failed to decode JSON stream chunk: {json_content}")
                                continue # Skip this chunk and try to process the next
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error during LLM communication: {e}")
            yield "" # Or raise an error
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred during streaming: {e}")
            yield "" # Or raise an error

    def get_params(self) -> Dict[str, Any]:
        """Returns a dictionary of all current model parameters."""
        return {
            self.PARAM_KEY_MAP["model"]: self.model,
            self.PARAM_KEY_MAP["temperature"]: self.temperature,
            self.PARAM_KEY_MAP["max_tokens"]: self.max_tokens,
            self.PARAM_KEY_MAP["stream"]: self.stream,
            self.PARAM_KEY_MAP["system_prompt"]: self.system_prompt,
            self.PARAM_KEY_MAP["top_p"]: self.top_p,
            self.PARAM_KEY_MAP["presence_penalty"]: self.presence_penalty,
            self.PARAM_KEY_MAP["frequency_penalty"]: self.frequency_penalty,
            self.PARAM_KEY_MAP["stop_sequences"]: self.stop_sequences.copy(),
            "api_base_url": API_BASE_URL # Add api_base_url to the parameters
        }

    def set_parameter(self, param_name: str, value: Any):
        """Sets a model parameter and saves it to user settings."""
        attr = param_name
        key = self.PARAM_KEY_MAP.get(attr, attr.upper())

        if not hasattr(self, attr):
            print(f"Error: Parameter '{param_name}' cannot be set on the client.")
            return False

        if key not in self.default_params:
            print(f"Error: Parameter '{param_name}' is not a recognized configurable parameter.")
            return False

        expected_type_source = self.default_params.get(key)

        try:
            current_actual_value = getattr(self, attr)
            if isinstance(current_actual_value, bool) and not isinstance(value, bool):
                if str(value).lower() == 'true': value_to_set = True
                elif str(value).lower() == 'false': value_to_set = False
                else: raise ValueError("Boolean parameter must be True or False")
            elif attr == "stop_sequences":
                if isinstance(value, str):
                    value_to_set = [seq.strip() for seq in value.split(',') if seq.strip()]
                elif isinstance(value, list):
                    value_to_set = value
                else: raise ValueError("stop_sequences must be a list or a comma-separated string.")
            elif attr == "system_prompt":
                value_to_set = str(value) if value is not None else None
            else:
                value_to_set = type(self.default_params[key])(value)

            setattr(self, attr, value_to_set)
            print(f"Parameter '{param_name}' set to: {value_to_set}")

            # Save all current settings (including the updated one)
            current_settings = self.get_all_parameters() # Get all current params
            save_user_settings(current_settings)
            print(f"Parameter '{param_name}' set to '{value}'.")
        except (ValueError, TypeError) as e:
            expected_type_name = type(expected_type_source).__name__ if expected_type_source is not None else "unknown"
            print(f"Error setting parameter '{param_name}': Invalid value type. Expected compatible with {expected_type_name}. Got '{value}'. Details: {e}")
            return False

    def set_system_prompt(self, prompt: Optional[str]):
        """Sets the system prompt and saves it."""
        self.system_prompt = prompt
        current_settings = self.get_all_parameters()
        current_settings[self.PARAM_KEY_MAP["system_prompt"]] = prompt
        save_user_settings(current_settings)
        if prompt:
            print(f"System prompt set to: '{prompt}'")
        else:
            print("System prompt cleared.")