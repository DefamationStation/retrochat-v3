"""
Handles communication with the LM Studio API.
"""
import requests
import json
import logging
from typing import Optional, List, Dict, Any

# Use the new configuration system
from retrochat_app.core.config import get_config
from retrochat_app.core import config_manager

logger = logging.getLogger(__name__)

class LLMClient:
    """
    A client for interacting with the LM Studio API.
    
    This client provides a clean interface to the LM Studio API while automatically
    staying synchronized with the application's configuration system.
    """

    def __init__(self):
        """Initialize the LLM client with configuration."""
        self.config = get_config()
        logger.info("LLM Client initialized")

    @property
    def endpoint(self) -> str:
        """Get the current API endpoint."""
        return self.config.api.chat_completions_endpoint

    def update_endpoint(self) -> None:
        """Updates the endpoint from the current config."""
        # Endpoint is now always current via the property
        logger.info(f"Endpoint updated to: {self.endpoint}")

    def _get_current_params_payload(self) -> Dict[str, Any]:
        """Helper to get payload-ready parameters from current config."""
        return self.config.model.get_api_parameters()

    def send_chat_message_full_history(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Sends a chat request with the complete message history (non-streaming)."""
        if not messages:
            logger.error("Message list cannot be empty")
            return None

        payload = self._get_current_params_payload()
        payload["messages"] = messages
        payload["stream"] = False  # Ensure stream is False for this method

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                self.endpoint, 
                headers=headers, 
                data=json.dumps(payload), 
                stream=False,
                timeout=self.config.api.timeout
            )
            response.raise_for_status()
            response_data = response.json()
            
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                # Check if 'message' key exists and has 'content'
                if "message" in response_data["choices"][0] and "content" in response_data["choices"][0]["message"]:
                    return response_data["choices"][0]["message"]["content"]
                # Fallback for models that might structure response differently
                elif "delta" in response_data["choices"][0] and "content" in response_data["choices"][0]["delta"]:
                    return response_data["choices"][0]["delta"]["content"]
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during LLM communication: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {response.text}")
            return None

    def stream_chat_message(self, messages: List[Dict[str, Any]]):
        """Sends a chat request and streams the response."""
        if not messages:
            logger.error("Message list cannot be empty")
            yield ""
            return

        payload = self._get_current_params_payload()
        payload["messages"] = messages
        payload["stream"] = True  # Ensure stream is True for this method

        headers = {"Content-Type": "application/json"}

        try:
            with requests.post(
                self.endpoint, 
                headers=headers, 
                data=json.dumps(payload), 
                stream=True,
                timeout=self.config.api.timeout
            ) as response:
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
                                logger.error(f"Failed to decode JSON stream chunk: {json_content}")
                                continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during LLM communication: {e}")
            yield ""
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            yield ""

    def get_params(self) -> Dict[str, Any]:
        """Returns a dictionary of all current model parameters."""
        result = self.config.get_model_parameters()
        result["api_base_url"] = self.config.api.base_url
        return result

    def get_all_parameters(self) -> Dict[str, Any]:
        """Alias for get_params() for backward compatibility."""
        return self.get_params()

    def set_parameter(self, param_name: str, value: Any) -> bool:
        """Sets a model or API parameter and saves it to user settings."""
        try:
            param_name_lower = param_name.lower()

            if param_name_lower == "api_ip_port":
                # Value should be "ip:port" or "http://ip:port"
                config_manager.update_api_base_url(str(value))
                # Refresh config
                from retrochat_app.core.config import get_config as refresh_get_config # Local import for refresh
                self.config = refresh_get_config()
                print(f"API IP/Port updated. New endpoint: {self.endpoint}")
                return True
            elif param_name_lower == "api_full_endpoint":
                config_manager.update_chat_completions_endpoint_direct(str(value))
                # Refresh config
                from retrochat_app.core.config import get_config as refresh_get_config # Local import for refresh
                self.config = refresh_get_config()
                print(f"API endpoint updated to: {self.endpoint}")
                return True
            elif param_name_lower == "endpoint":
                # This case is now deprecated in favor of api_ip_port and api_full_endpoint
                # For backward compatibility, or if other parts of code use it,
                # we could map it to one of the new ones, e.g., full_endpoint.
                # However, per user request, we are introducing specific commands.
                # So, we can choose to make this an error or map it.
                # For now, let's assume it's an error or no-op if called directly.
                print(f"Warning: Setting 'endpoint' directly is deprecated. Use '/set ip' or '/set endpoint <full_url>'.")
                # Or, if we want to map it:
                # config_manager.update_chat_completions_endpoint_direct(str(value))
                # from retrochat_app.core.config import get_config as refresh_get_config
                # self.config = refresh_get_config()
                # print(f"API endpoint updated to: {self.endpoint} (via deprecated 'endpoint' param)")
                return False # Or True if mapped
            
            # Handle model parameters (existing logic)
            # Ensure self.config has update_model_parameter or similar
            if hasattr(self.config, 'update_model_parameter'):
                self.config.update_model_parameter(param_name, value)
                print(f"Model parameter '{param_name}' set to: {value}")
                return True
            else:
                # Fallback for other parameters if not model parameters handled by self.config
                # This part might need adjustment based on how self.config handles general params
                # For now, assume model parameters are the primary target for this path.
                # If 'stream' is handled here, it should be.
                if param_name_lower == "stream": # Example: if stream is a model param
                    if hasattr(self.config, 'update_model_parameter'):
                         self.config.update_model_parameter(param_name_lower, bool(value)) # Ensure boolean
                         print(f"Model parameter '{param_name_lower}' set to: {bool(value)}")
                         return True
                    else: # if stream is handled differently, e.g. directly on config.model
                        if hasattr(self.config, 'model') and hasattr(self.config.model, param_name_lower):
                            setattr(self.config.model, param_name_lower, bool(value))
                            # Assuming self.config.save() or similar is called by update_model_parameter
                            # If not, direct attribute setting might not persist.
                            # This part is speculative without seeing config.py's Config class.
                            # For safety, let's assume update_model_parameter is the way.
                            print(f"Parameter '{param_name_lower}' (potentially model) set to: {bool(value)}")
                            return True

                print(f"Parameter '{param_name}' (not API, not model) not explicitly handled by set_parameter.")
                return False

        except ValueError as e:
            print(f"Error setting parameter '{param_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting parameter '{param_name}': {e}")
            print(f"Error setting parameter '{param_name}': {e}")
            return False

    def set_system_prompt(self, prompt: Optional[str]) -> None:
        """Sets the system prompt and saves it."""
        try:
            self.config.update_model_parameter("system_prompt", prompt)
            if prompt:
                print(f"System prompt set to: '{prompt}'")
            else:
                print("System prompt cleared.")
        except Exception as e:
            logger.error(f"Error setting system prompt: {e}")
            print(f"Error setting system prompt: {e}")

    # Backward compatibility properties
    @property
    def model(self) -> str:
        """Get current model name."""
        return self.config.model.model_name

    @property
    def temperature(self) -> float:
        """Get current temperature."""
        return self.config.model.temperature

    @property
    def max_tokens(self) -> int:
        """Get current max tokens."""
        return self.config.model.max_tokens

    @property
    def stream(self) -> bool:
        """Get current stream setting."""
        return self.config.model.stream

    @property
    def system_prompt(self) -> Optional[str]:
        """Get current system prompt."""
        return self.config.model.system_prompt

    @property
    def top_p(self) -> float:
        """Get current top_p."""
        return self.config.model.top_p

    @property
    def presence_penalty(self) -> float:
        """Get current presence penalty."""
        return self.config.model.presence_penalty

    @property
    def frequency_penalty(self) -> float:
        """Get current frequency penalty."""
        return self.config.model.frequency_penalty

    @property
    def stop_sequences(self) -> List[str]:
        """Get current stop sequences."""
        return self.config.model.stop_sequences