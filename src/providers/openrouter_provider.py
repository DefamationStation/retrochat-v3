"""
OpenRouter provider implementation.

This provider connects to OpenRouter's API which provides access to
hundreds of AI models through a unified interface.
"""

from typing import List, Dict, Any, Iterator
from openai import OpenAI
from .base_provider import BaseProvider, BaseModelManager, BaseChat
import requests


class OpenRouterModelManager(BaseModelManager):
    """Model manager for OpenRouter."""
    
    def __init__(self, client: OpenAI, api_key: str):
        self.client = client
        self.api_key = api_key
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from OpenRouter."""
        try:
            # Use OpenRouter's models API endpoint
            headers = {
                'Authorization': f'Bearer {self.api_key}',
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
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        models = self.get_models()
        for model in models:
            if model['id'] == model_id:
                return model
        return {}


class OpenRouterChat(BaseChat):
    """Chat implementation for OpenRouter."""
    
    def __init__(self, client: OpenAI, config: Dict[str, Any]):
        self.client = client
        self.config = config
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare OpenRouter-specific headers."""
        headers = {}
        
        # Optional headers for OpenRouter leaderboards
        if 'site_url' in self.config:
            headers['HTTP-Referer'] = self.config['site_url']
        if 'site_name' in self.config:
            headers['X-Title'] = self.config['site_name']
            
        return headers
    
    def send_message(self, message: str, history: List[Dict[str, Any]], **kwargs) -> str:
        """Send a message to OpenRouter and get response."""
        try:
            # Prepare the messages
            messages = history.copy()
            
            # Add system message if not present and system_prompt is configured
            if not any(msg.get('role') == 'system' for msg in messages):
                system_prompt = self.config.get('system_prompt')
                if system_prompt:
                    messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Get model from config
            model = self.config.get('default_model')
            if not model:
                raise ValueError("No default model configured")
            
            # Prepare parameters
            params = {
                'model': model,
                'messages': messages,
                'temperature': kwargs.get('temperature', 0.7),
                'stream': False
            }
            
            # Add optional parameters if provided
            if 'max_tokens' in kwargs:
                params['max_tokens'] = kwargs['max_tokens']
            if 'top_p' in kwargs:
                params['top_p'] = kwargs['top_p']
            
            # Add OpenRouter-specific headers
            extra_headers = self._prepare_headers()
            
            completion = self.client.chat.completions.create(
                extra_headers=extra_headers,
                **params
            )
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def send_message_stream(self, message: str, history: List[Dict[str, Any]], **kwargs) -> Iterator[str]:
        """Send a message to OpenRouter and get streaming response."""
        try:
            # Prepare the messages
            messages = history.copy()
            
            # Add system message if not present and system_prompt is configured
            if not any(msg.get('role') == 'system' for msg in messages):
                system_prompt = self.config.get('system_prompt')
                if system_prompt:
                    messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Get model from config
            model = self.config.get('default_model')
            if not model:
                raise ValueError("No default model configured")
            
            # Prepare parameters
            params = {
                'model': model,
                'messages': messages,
                'temperature': kwargs.get('temperature', 0.7),
                'stream': True
            }
            
            # Add optional parameters if provided
            if 'max_tokens' in kwargs:
                params['max_tokens'] = kwargs['max_tokens']
            if 'top_p' in kwargs:
                params['top_p'] = kwargs['top_p']
            
            # Add OpenRouter-specific headers
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


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider implementation."""
    
    def get_provider_name(self) -> str:
        return "openrouter"
    
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
        
        # Validate API key format (should start with sk-)
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
            
            # Test with a simple models request
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"OpenRouter connection test failed: {e}")
            return False
    
    def create_model_manager(self) -> BaseModelManager:
        """Create OpenRouter model manager."""
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.config['api_key']
        )
        return OpenRouterModelManager(client, self.config['api_key'])
    
    def create_chat(self) -> BaseChat:
        """Create OpenRouter chat."""
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.config['api_key']
        )
        return OpenRouterChat(client, self.config)
