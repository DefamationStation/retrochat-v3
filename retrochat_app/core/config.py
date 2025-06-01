"""
Configuration bridge for the LM Studio Chat Application.
This module provides a unified configuration interface.
"""
import re
from typing import Dict, Any, List, Optional
from . import config_manager


class APIConfig:
    """API configuration handler."""
    
    def __init__(self):
        self.timeout = 30  # Default timeout
    
    @property
    def base_url(self) -> str:
        """Get the base API URL."""
        settings = config_manager.load_user_settings()
        return settings.get("api_base_url", config_manager.API_BASE_URL)
    
    @property
    def chat_completions_endpoint(self) -> str:
        """Get the chat completions endpoint."""
        return f"{self.base_url}/v1/chat/completions"
    
    def _validate_ip_port(self, ip_port: str) -> bool:
        """Validate IP:PORT format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}:\d+$'
        return bool(re.match(pattern, ip_port))


class ModelConfig:
    """Model configuration handler."""
    
    def __init__(self):
        self._settings = {}
        self.reload_settings()
    
    def reload_settings(self):
        """Reload settings from the config manager."""
        defaults = config_manager.get_default_settings()
        user_settings = config_manager.load_user_settings()
        self._settings = {**defaults, **user_settings}
    
    @property
    def model_name(self) -> str:
        return self._settings.get("model_name", "local-model")
    
    @property
    def temperature(self) -> float:
        return self._settings.get("temperature", 0.7)
    
    @property
    def max_tokens(self) -> int:
        return self._settings.get("max_tokens", 500)
    
    @property
    def stream(self) -> bool:
        return self._settings.get("stream", False)
    
    @property
    def system_prompt(self) -> Optional[str]:
        return self._settings.get("system_prompt")
    
    @property
    def top_p(self) -> float:
        return self._settings.get("top_p", 0.95)
    
    @property
    def presence_penalty(self) -> float:
        return self._settings.get("presence_penalty", 0.0)
    
    @property
    def frequency_penalty(self) -> float:
        return self._settings.get("frequency_penalty", 0.0)
    
    @property
    def stop_sequences(self) -> List[str]:
        return self._settings.get("stop_sequences", [])
    
    def get_api_parameters(self) -> Dict[str, Any]:
        """Get parameters for API calls."""
        params = {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }
        
        if self.system_prompt:
            params["system_prompt"] = self.system_prompt
        
        if self.stop_sequences:
            params["stop"] = self.stop_sequences
            
        return params


class Configuration:
    """Main configuration class."""
    
    def __init__(self):
        self.api = APIConfig()
        self.model = ModelConfig()
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """Get all model parameters."""
        return self.model.get_api_parameters()
    
    def update_model_parameter(self, param_name: str, value: Any) -> None:
        """Update a model parameter and save it."""
        current_settings = config_manager.load_user_settings()
        current_settings[param_name] = value
        config_manager.save_user_settings(current_settings)
        self.model.reload_settings()
    
    def update_api_endpoint(self, ip_port: str) -> None:
        """Update the API endpoint."""
        config_manager.update_api_base_url(ip_port)
        # Recreate API config to pick up new URL
        self.api = APIConfig()


def get_config() -> Configuration:
    """Get the global configuration instance."""
    return Configuration()
