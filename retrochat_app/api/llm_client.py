"""
Handles communication with the LM Studio API.
"""
import requests
import json
from typing import Optional, List, Dict, Any
# Adjusted import path for config
from retrochat_app.core.config_manager import (
    CHAT_COMPLETIONS_ENDPOINT, MODEL_NAME, TEMPERATURE, MAX_TOKENS, STREAM,
    SYSTEM_PROMPT, TOP_P, PRESENCE_PENALTY, FREQUENCY_PENALTY, STOP_SEQUENCES
)

class LLMClient:
    """
    A client for interacting with the LM Studio API.
    """
    def __init__(self):
        self.endpoint = CHAT_COMPLETIONS_ENDPOINT
        
        self.default_params = {
            "model": MODEL_NAME,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "stream": STREAM,
            "system_prompt": SYSTEM_PROMPT,
            "top_p": TOP_P,
            "presence_penalty": PRESENCE_PENALTY,
            "frequency_penalty": FREQUENCY_PENALTY,
            "stop_sequences": STOP_SEQUENCES.copy()
        }

        self.model = MODEL_NAME
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS
        self.stream = STREAM
        self.system_prompt = SYSTEM_PROMPT
        self.top_p = TOP_P
        self.presence_penalty = PRESENCE_PENALTY
        self.frequency_penalty = FREQUENCY_PENALTY
        self.stop_sequences = STOP_SEQUENCES.copy()

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

    def set_parameter(self, param_name: str, value: Any) -> bool:
        if not hasattr(self, param_name):
            print(f"Error: Parameter '{param_name}' cannot be set on the client.")
            return False

        if param_name not in self.default_params and not hasattr(self, param_name):
             print(f"Error: Parameter '{param_name}' is not a recognized configurable parameter.")
             return False
        
        expected_type_source = self.default_params.get(param_name, getattr(self, param_name, None))
        if expected_type_source is None and param_name != "system_prompt":
            print(f"Error: Could not determine expected type for parameter '{param_name}'.")
            return False

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
                value_to_set = type(current_actual_value)(value)
           
            setattr(self, param_name, value_to_set)
            print(f"Parameter '{param_name}' set to: {value_to_set}")
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

    def add_stop_sequence(self, sequence: str):
        if sequence not in self.stop_sequences:
            self.stop_sequences.append(sequence)
            print(f'Added stop sequence: "{sequence}"')
        else:
            print(f'Stop sequence "{sequence}" already exists.')

    def remove_stop_sequence(self, sequence: str):
        if sequence in self.stop_sequences:
            self.stop_sequences.remove(sequence)
            print(f'Removed stop sequence: "{sequence}"')
        else:
            print(f'Stop sequence "{sequence}" not found.')
    
    def clear_stop_sequences(self):
        self.stop_sequences = []
        print("All stop sequences cleared.")

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
