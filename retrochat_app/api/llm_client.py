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
    def __init__(self):
        self.endpoint = CHAT_COMPLETIONS_ENDPOINT
        
        # Load default settings first
        self.default_params = get_default_settings()
        
        # Load user settings and override defaults
        user_settings = load_user_settings()
        
        # Initialize attributes from defaults, then update with user settings
        self.model = user_settings.get("MODEL_NAME", self.default_params["MODEL_NAME"])
        self.temperature = user_settings.get("TEMPERATURE", self.default_params["TEMPERATURE"])
        self.max_tokens = user_settings.get("MAX_TOKENS", self.default_params["MAX_TOKENS"])
        self.stream = user_settings.get("STREAM", self.default_params["STREAM"])
        self.system_prompt = user_settings.get("SYSTEM_PROMPT", self.default_params["SYSTEM_PROMPT"])
        self.top_p = user_settings.get("TOP_P", self.default_params["TOP_P"])
        self.presence_penalty = user_settings.get("PRESENCE_PENALTY", self.default_params["PRESENCE_PENALTY"])
        self.frequency_penalty = user_settings.get("FREQUENCY_PENALTY", self.default_params["FREQUENCY_PENALTY"])
        self.stop_sequences = user_settings.get("STOP_SEQUENCES", self.default_params["STOP_SEQUENCES"]).copy()

        # Update default_params to reflect the actual initial state (after user settings)
        # This is important if set_parameter compares against default_params later
        self.default_params["MODEL_NAME"] = self.model
        self.default_params["TEMPERATURE"] = self.temperature
        self.default_params["MAX_TOKENS"] = self.max_tokens
        self.default_params["STREAM"] = self.stream
        self.default_params["SYSTEM_PROMPT"] = self.system_prompt
        self.default_params["TOP_P"] = self.top_p
        self.default_params["PRESENCE_PENALTY"] = self.presence_penalty
        self.default_params["FREQUENCY_PENALTY"] = self.frequency_penalty
        self.default_params["STOP_SEQUENCES"] = self.stop_sequences.copy()


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
        # Map attribute names to the keys used in settings files if they differ
        # For example, if the attribute is self.model but in JSON it's MODEL_NAME
        settings_key_map = {
            "model": "MODEL_NAME",
            "temperature": "TEMPERATURE",
            "max_tokens": "MAX_TOKENS",
            "stream": "STREAM",
            "system_prompt": "SYSTEM_PROMPT",
            "top_p": "TOP_P",
            "presence_penalty": "PRESENCE_PENALTY",
            "frequency_penalty": "FREQUENCY_PENALTY",
            "stop_sequences": "STOP_SEQUENCES"
        }

        # Determine the correct key for saving to user_settings.json
        save_key = settings_key_map.get(param_name, param_name.upper()) # Default to uppercase if not in map

        # Original validation and type conversion logic
        if not hasattr(self, param_name):
            print(f"Error: Parameter '{param_name}' cannot be set on the client.")
            return False

        # Check against the keys in default_params for recognized configurable parameters
        if param_name not in self.default_params:
             print(f"Error: Parameter '{param_name}' is not a recognized configurable parameter.")
             return False
        
        expected_type_source = self.default_params.get(param_name)

        try:
            current_actual_value = getattr(self, param_name)
            if isinstance(current_actual_value, bool) and not isinstance(value, bool):
                if str(value).lower() == 'true': value_to_set = True
                elif str(value).lower() == 'false': value_to_set = False
                else: raise ValueError("Boolean parameter must be True or False")
            elif param_name == "stop_sequences":
                if isinstance(value, str):
                    value_to_set = [seq.strip() for seq in value.split(',') if seq.strip()]
                elif isinstance(value, list):
                    value_to_set = value
                else: raise ValueError("stop_sequences must be a list or a comma-separated string.")
            elif param_name == "system_prompt":
                 value_to_set = str(value) if value is not None else None
            else:
                # Use the type of the value in default_params for conversion
                value_to_set = type(self.default_params[param_name])(value)
           
            setattr(self, param_name, value_to_set)
            print(f"Parameter '{param_name}' set to: {value_to_set}")

            # Save the updated settings
            user_settings = load_user_settings() # Load current to preserve other settings
            user_settings[save_key] = value_to_set # Use the mapped key
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
        # Save the updated system prompt
        user_settings = load_user_settings()
        user_settings["SYSTEM_PROMPT"] = prompt
        save_user_settings(user_settings)

    def get_all_parameters(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
            "system_prompt": self.system_prompt,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop_sequences": self.stop_sequences.copy(),
        }

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
