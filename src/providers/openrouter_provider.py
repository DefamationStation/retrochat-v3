"""
OpenRouter provider implementation.

This provider connects to OpenRouter's API which provides access to
hundreds of AI models through a unified interface.
"""

from typing import List, Dict, Any
from openai import OpenAI
import requests
from .base_openai_provider import BaseOpenAIProvider, BaseOpenAIModelManager, BaseOpenAIChat


class OpenRouterModelManager(BaseOpenAIModelManager):
    """Model manager for OpenRouter."""

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from OpenRouter."""
        try:
            headers = {
                'Authorization': f'Bearer {self.client.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                for model in data.get('data', []):
                    models.append({
                        'id': model.get('id', ''),
                        'name': model.get('name', model.get('id', '')),
                        'description': model.get('description', ''),
                        'context_length': model.get('context_length', 0),
                        'pricing': model.get('pricing', {}),
                        'created': model.get('created'),
                        'owned_by': 'openrouter',
                        'architecture': model.get('architecture', {}),
                        'top_provider': model.get('top_provider', {}),
                    })
                
                return models
            else:
                print(f"Error fetching models from OpenRouter: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching models from OpenRouter: {e}")
            return []


class OpenRouterChat(BaseOpenAIChat):
    """Chat implementation for OpenRouter."""

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare OpenRouter-specific headers."""
        headers = {}
        
        if 'site_url' in self.config:
            headers['HTTP-Referer'] = self.config['site_url']
        if 'site_name' in self.config:
            headers['X-Title'] = self.config['site_name']
            
        return headers

    def send_message(self, message: str, history: List[Dict[str, Any]], **kwargs) -> str:
        """Send a message to OpenRouter and get response."""
        try:
            messages = self._prepare_messages(message, history)
            params = self._prepare_params(messages, stream=False, **kwargs)
            extra_headers = self._prepare_headers()
            
            completion = self.client.chat.completions.create(
                extra_headers=extra_headers,
                **params
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def send_message_stream(self, message: str, history: List[Dict[str, Any]], **kwargs) -> str:
        """Send a message to OpenRouter and get streaming response."""
        try:
            messages = self._prepare_messages(message, history)
            params = self._prepare_params(messages, stream=True, **kwargs)
            extra_headers = self._prepare_headers()
            
            completion = self.client.chat.completions.create(
                extra_headers=extra_headers,
                **params
            )
            
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"Error: {str(e)}"


class OpenRouterProvider(BaseOpenAIProvider):
    """OpenRouter provider implementation."""
    
    def get_provider_name(self) -> str:
        return "openrouter"

    def get_api_base(self) -> str:
        return "https://openrouter.ai/api/v1"

    def get_required_config_keys(self) -> List[str]:
        return ["api_key"]

    def get_optional_config_keys(self) -> List[str]:
        return [
            "default_model", "system_prompt", "stream", "temperature", 
            "max_tokens", "top_p", "site_url", "site_name"
        ]

    def validate_config(self) -> bool:
        """Validate OpenRouter configuration."""
        required_keys = self.get_required_config_keys()
        
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                print(f"Missing required configuration key: {key}")
                return False
        
        api_key = self.config.get('api_key', '')
        if not api_key.startswith('sk-'):
            print("OpenRouter API key should start with 'sk-'")
            return False
        
        return True

    def test_connection(self) -> bool:
        """Test connection to OpenRouter."""
        try:
            headers = {
                'Authorization': f'Bearer {self.config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"OpenRouter connection test failed: {e}")
            return False

    def create_model_manager(self) -> BaseOpenAIModelManager:
        """Create OpenRouter model manager."""
        return OpenRouterModelManager(self.get_client())

    def create_chat(self) -> BaseOpenAIChat:
        """Create OpenRouter chat."""
        return OpenRouterChat(self.get_client(), self.config)
