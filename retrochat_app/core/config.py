"""
Configuration bridge for the LM Studio Chat Application.
This module provides a unified configuration interface.
"""
import re
from typing import Dict, Any, List, Optional
from . import config_manager
from retrochat_app.core import provider_manager


class APIConfig:
    """API configuration handler."""
    
    def __init__(self):
        self.timeout = 30  # Default timeout
    
    @property
    def base_url(self) -> str:
        """Get the base API URL, preferring active provider config."""
        provider = provider_manager.get_active_provider()
        if provider and provider.get("api_base_url"):
            return provider.get("api_base_url")
        settings = config_manager.load_user_settings()
        return settings.get("api_base_url", config_manager.API_BASE_URL)
    
    @property
    def chat_completions_endpoint(self) -> str:
        """Get the chat completions endpoint, preferring active provider config."""
        provider = provider_manager.get_active_provider()
        if provider and provider.get("chat_completions_endpoint"):
            return provider.get("chat_completions_endpoint")
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

    # Additional optional parameters used by some providers

    @property
    def num_ctx(self) -> Optional[int]:
        return self._settings.get("num_ctx")

    @property
    def top_k(self) -> Optional[int]:
        return self._settings.get("top_k")

    @property
    def min_p(self) -> Optional[float]:
        return self._settings.get("min_p")

    @property
    def typical_p(self) -> Optional[float]:
        return self._settings.get("typical_p")

    @property
    def repeat_penalty(self) -> Optional[float]:
        return self._settings.get("repeat_penalty")

    @property
    def repeat_last_n(self) -> Optional[int]:
        return self._settings.get("repeat_last_n")

    @property
    def seed(self) -> Optional[int]:
        return self._settings.get("seed")

    @property
    def num_keep(self) -> Optional[int]:
        return self._settings.get("num_keep")

    @property
    def penalize_newline(self) -> Optional[bool]:
        return self._settings.get("penalize_newline")

    @property
    def numa(self) -> Optional[bool]:
        return self._settings.get("numa")

    @property
    def num_batch(self) -> Optional[int]:
        return self._settings.get("num_batch")

    @property
    def num_gpu(self) -> Optional[int]:
        return self._settings.get("num_gpu")

    @property
    def main_gpu(self) -> Optional[int]:
        return self._settings.get("main_gpu")

    @property
    def use_mmap(self) -> Optional[bool]:
        return self._settings.get("use_mmap")

    @property
    def num_thread(self) -> Optional[int]:
        return self._settings.get("num_thread")

    @property
    def keep_alive(self) -> Optional[str]:
        return self._settings.get("keep_alive")
    
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

        # Optional advanced parameters
        optional_map = {
            "num_ctx": self.num_ctx,
            "top_k": self.top_k,
            "min_p": self.min_p,
            "typical_p": self.typical_p,
            "repeat_penalty": self.repeat_penalty,
            "repeat_last_n": self.repeat_last_n,
            "seed": self.seed,
            "num_keep": self.num_keep,
            "penalize_newline": self.penalize_newline,
            "numa": self.numa,
            "num_batch": self.num_batch,
            "num_gpu": self.num_gpu,
            "main_gpu": self.main_gpu,
            "use_mmap": self.use_mmap,
            "num_thread": self.num_thread,
            "keep_alive": self.keep_alive,
        }
        for key, value in optional_map.items():
            if value is not None:
                params[key] = value

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
