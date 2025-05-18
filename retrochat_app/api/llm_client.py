"""
Handles communication with the LM Studio API.
"""
import requests
import json
from typing import Optional, List, Dict, Any
# Adjusted import path for config
from retrochat_app.core.config_manager import (
    CHAT_COMPLETIONS_ENDPOINT, # Keep existing imports
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

    def send_chat_message(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None):
        """
        Original method to send a chat message. 
        Consider this for single-turn or if you prefer managing history outside before calling.
        For continuous chat, use send_chat_message_full_history or stream_chat_message.
        """
        processed_messages = []
        if self.system_prompt:
            processed_messages.append({"role": "system", "content": self.system_prompt})

        if conversation_history:
            processed_messages.extend(conversation_history)
        
        processed_messages.append({"role": "user", "content": user_message})

        payload = self._get_current_params_payload()
        payload["messages"] = processed_messages

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.endpoint, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            response_data = response.json()
            
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                assistant_message = response_data["choices"][0].get("message", {}).get("content")
                return assistant_message
            else:
                print("Error: No response choices found in API reply.")
                print("Full response:", response_data)
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to LM Studio: {e}")
            return None
        except json.JSONDecodeError:
            print("Error: Could not decode JSON response from API.")
            print("Raw response:", response.text)
            return None

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
                assistant_message = response_data["choices"][0].get("message", {}).get("content")
                return assistant_message
            else:
                print("Error: No response choices found in API reply.")
                print("Full response:", response_data)
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to LM Studio: {e}")
            return None
        except json.JSONDecodeError:
            print("Error: Could not decode JSON response from API.")
            print("Raw response:", response.text)
            return None

    def stream_chat_message(self, messages: List[Dict[str, Any]]):
        """Sends a chat request with the complete message history (streaming)."""
        if not messages:
            print("Error: Message list cannot be empty.")
            yield "Error: Message list cannot be empty." # Yield error message
            return

        payload = self._get_current_params_payload()
        payload["messages"] = messages # Use the provided full history
        payload["stream"] = True # Ensure stream is True for this method

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(self.endpoint, headers=headers, data=json.dumps(payload), stream=True)
            response.raise_for_status()
            client = None # Placeholder for SSEClient if we use it
            # Check for SSE content type if your server explicitly sets it for streams
            # if 'text/event-stream' in response.headers.get("Content-Type", ""):
            #    client = SSEClient(response) # Requires sseclient-py library
            #    for event in client:
            #        if event.data:
            #            try:
            #                chunk_data = json.loads(event.data)
            #                if chunk_data.get("choices") and len(chunk_data["choices"]) > 0:
            #                    delta = chunk_data["choices"][0].get("delta", {}).get("content")
            #                    if delta:
            #                        yield delta
            #            except json.JSONDecodeError:
            #                # print(f"Non-JSON data in stream: {event.data}") # Optional: log non-JSON data
            #                pass # Ignore non-JSON parts like [DONE]
            # else:
                # Manual chunk processing if not using SSEClient or server sends raw chunks
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "): # Standard SSE format
                        json_data_part = decoded_line[len("data: "):]
                        if json_data_part.strip() == "[DONE]": # LM Studio specific end signal
                            break
                        try:
                            chunk_data = json.loads(json_data_part)
                            if chunk_data.get("choices") and len(chunk_data["choices"]) > 0:
                                delta = chunk_data["choices"][0].get("delta", {}).get("content")
                                if delta:
                                    yield delta
                        except json.JSONDecodeError:
                            # print(f"Skipping non-JSON line: {decoded_line}") # For debugging
                            pass # Ignore lines that are not valid JSON

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to LM Studio for streaming: {e}")
            yield f" Error: {e}"
        except Exception as e:
            print(f"An unexpected error occurred during streaming: {e}")
            yield f" Error: {e}"

    def set_parameter(self, param_name: str, value: Any) -> bool:
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

            # Save the updated settings
            user_settings = load_user_settings()
            user_settings[key] = value_to_set
            save_user_settings(user_settings)
            return True
        except (ValueError, TypeError) as e:
            expected_type_name = type(expected_type_source).__name__ if expected_type_source is not None else "unknown"
            print(f"Error setting parameter '{param_name}': Invalid value type. Expected compatible with {expected_type_name}. Got '{value}'. Details: {e}")
            return False

    def set_system_prompt(self, prompt: Optional[str]):
        self.system_prompt = prompt
        if prompt:
            print(f'System prompt set to: "{prompt}"')
        else:
            print("System prompt cleared.")
        # Save the updated system prompt using the mapping
        user_settings = load_user_settings()
        user_settings[self.PARAM_KEY_MAP["system_prompt"]] = prompt
        save_user_settings(user_settings)

    def get_all_parameters(self) -> Dict[str, Any]:
        # Return parameters using the user settings keys for consistency
        params = {}
        for attr, key in self.PARAM_KEY_MAP.items():
            val = getattr(self, attr)
            # Copy list for stop_sequences
            if attr == "stop_sequences":
                val = val.copy() if isinstance(val, list) else val
            params[key] = val
        return params

# Example usage (for testing this module directly)
if __name__ == '__main__':
    client = LLMClient()
    history = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."}
    ]
    user_input = "And what is its population?"
    print(f"User: {user_input}")
    response = client.send_chat_message(user_input, conversation_history=history)
    if response:
        print(f"LLM: {response}")