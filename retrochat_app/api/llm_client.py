"""
Handles communication with the LM Studio API.
"""
import requests
import json
import logging
from typing import Optional, List, Dict, Any

# Use the new configuration system
from retrochat_app.core.config import get_config
from retrochat_app.core import config_manager, provider_manager
from retrochat_app.api.providers import get_provider_handler

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
        """Helper to get payload-ready parameters merging provider defaults."""
        user_params = self.config.model.get_api_parameters()
        provider = provider_manager.get_active_provider()
        provider_params = provider.get("params", {}) if provider else {}
        # Provider defaults are overridden by user-specified parameters
        return {**provider_params, **user_params}



    def _get_provider(self):
        cfg = provider_manager.get_active_provider()
        return get_provider_handler(cfg, self.config)

    def send_chat_message_full_history(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Sends a chat request with the complete message history (non-streaming)."""
        if not messages:
            logger.error("Message list cannot be empty")
            return None

        provider = self._get_provider()
        params = self._get_current_params_payload()
        headers = provider.build_headers()
        payload = provider.build_payload(messages, params, stream=False)
        endpoint = provider.build_endpoint()

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                data=json.dumps(payload),
                stream=False,
                timeout=self.config.api.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return provider.parse_response(data)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during LLM communication: {e}")
            return None
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response")
            return None
            

    def stream_chat_message(self, messages: List[Dict[str, Any]]):
        """Sends a chat request and streams the response."""
        if not messages:
            logger.error("Message list cannot be empty")
            yield ""
            return

        provider = self._get_provider()
        params = self._get_current_params_payload()
        headers = provider.build_headers()
        payload = provider.build_payload(messages, params, stream=True)
        endpoint = provider.build_endpoint()

        try:
            with requests.post(
                endpoint,
                headers=headers,
                data=json.dumps(payload),
                stream=True,
                timeout=self.config.api.timeout,
            ) as response:
                response.raise_for_status()
                for text in provider.iter_stream(response):
                    yield text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during LLM communication: {e}")
            yield ""
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            yield ""

    def get_params(self) -> Dict[str, Any]:
        """Returns a dictionary of all current model and API parameters by fetching from config."""
        # Get model parameters from the config object, which should be up-to-date
        model_params = self.config.get_model_parameters() # This should reflect current settings
        
        # Add API specific parameters from the config object
        # These are not part of KNOWN_MODEL_PARAMS but are relevant for display/info
        # and are managed by config_manager directly or via Config object.
        api_params = {
            "api_base_url": self.config.api.base_url,
            "chat_completions_endpoint": self.config.api.chat_completions_endpoint,
            "api_timeout": self.config.api.timeout
        }
        
        # Combine model and API parameters
        # Model parameters from config.get_model_parameters() should be authoritative for model settings
        # API parameters are added for informational purposes when using /show params
        # Ensure no unintentional overwrites if keys were to overlap (though they shouldn't here)
        combined_params = {**model_params, **api_params}
        return combined_params

    def get_all_parameters(self) -> Dict[str, Any]:
        """Alias for get_params() for backward compatibility."""
        return self.get_params()

    def set_parameter(self, param_name: str, value: Any) -> bool:
        """Sets a model or API parameter by delegating to config_manager."""
        param_name_lower = param_name.lower()

        if param_name_lower == "api_ip_port":
            if config_manager.update_api_base_url(str(value)):
                self.config = get_config() # Refresh config
                logger.info(f"API IP/Port updated via config_manager. New endpoint: {self.endpoint}")
                print(f"API IP/Port updated. New endpoint: {self.endpoint}")
                return True
            return False
        elif param_name_lower == "api_full_endpoint":
            if config_manager.update_chat_completions_endpoint_direct(str(value)):
                self.config = get_config() # Refresh config
                logger.info(f"API full endpoint updated via config_manager. New endpoint: {self.endpoint}")
                print(f"API endpoint updated to: {self.endpoint}")
                return True
            return False
        elif param_name_lower == "endpoint": # Deprecated
            logger.warning("Setting 'endpoint' directly is deprecated. Use '/set ip' or '/set endpoint <full_url>'.")
            print("Warning: Setting 'endpoint' directly is deprecated. Use '/set ip' or '/set endpoint <full_url>'.")
            return False
        else:
            # Delegate to the new update_model_parameter in config_manager
            if config_manager.update_model_parameter(param_name, value):
                self.config = get_config() # Refresh config to reflect changes
                logger.info(f"Parameter '{param_name}' set to '{value}' via config_manager.")
                # The print statement is now handled by update_model_parameter
                return True
            else:
                # update_model_parameter will log and print errors
                logger.warning(f"Failed to set parameter '{param_name}' via config_manager.")
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