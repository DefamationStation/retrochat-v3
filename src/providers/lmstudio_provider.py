"""
LM Studio provider implementation.

This provider connects to LM Studio's local API server which provides
an OpenAI-compatible interface.
"""

from typing import List
from .base_openai_provider import BaseOpenAIProvider, BaseOpenAIModelManager, BaseOpenAIChat


class LMStudioModelManager(BaseOpenAIModelManager):
    """Model manager for LM Studio."""
    pass


class LMStudioChat(BaseOpenAIChat):
    """Chat implementation for LM Studio."""
    pass


class LMStudioProvider(BaseOpenAIProvider):
    """LM Studio provider implementation."""
    
    def get_provider_name(self) -> str:
        return "lmstudio"

    def get_api_base(self) -> str:
        return self.config.get('api_base', 'http://localhost:1234/v1')

    def get_required_config_keys(self) -> List[str]:
        return ["api_base", "api_key"]

    def get_optional_config_keys(self) -> List[str]:
        return ["default_model", "system_prompt", "stream", "temperature", "max_tokens", "top_p"]

    def validate_config(self) -> bool:
        """Validate LM Studio configuration."""
        required_keys = self.get_required_config_keys()
        
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                print(f"Missing required configuration key: {key}")
                return False
        
        api_base = self.config.get('api_base', '')
        if not api_base.startswith(('http://', 'https://')):
            print("api_base must be a valid HTTP URL")
            return False
        
        return True

    def create_model_manager(self) -> BaseOpenAIModelManager:
        """Create LM Studio model manager."""
        return LMStudioModelManager(self.get_client())

    def create_chat(self) -> BaseOpenAIChat:
        """Create LM Studio chat."""
        return LMStudioChat(self.get_client(), self.config)
