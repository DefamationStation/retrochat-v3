"""
LM Studio provider implementation.

This provider connects to LM Studio's local API server which provides
an OpenAI-compatible interface.
"""

from typing import List, Dict, Any, Iterator
from openai import OpenAI
from .base_provider import BaseProvider, BaseModelManager, BaseChat


class LMStudioModelManager(BaseModelManager):
    """Model manager for LM Studio."""
    
    def __init__(self, client: OpenAI):
        self.client = client
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from LM Studio."""
        try:
            models_response = self.client.models.list()
            models = []
            for model in models_response.data:
                models.append({
                    'id': model.id,
                    'name': model.id,  # LM Studio uses ID as display name
                    'object': getattr(model, 'object', 'model'),
                    'created': getattr(model, 'created', None),
                    'owned_by': getattr(model, 'owned_by', 'lm-studio'),
                })
            return models
        except Exception as e:
            print(f"Error fetching models from LM Studio: {e}")
            return []
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        models = self.get_models()
        for model in models:
            if model['id'] == model_id:
                return model
        return {}


class LMStudioChat(BaseChat):
    """Chat implementation for LM Studio."""
    
    def __init__(self, client: OpenAI, config: Dict[str, Any]):
        self.client = client
        self.config = config
    
    def send_message(self, message: str, history: List[Dict[str, Any]], **kwargs) -> str:
        """Send a message to LM Studio and get response."""
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
            
            completion = self.client.chat.completions.create(**params)
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def send_message_stream(self, message: str, history: List[Dict[str, Any]], **kwargs) -> Iterator[str]:
        """Send a message to LM Studio and get streaming response."""
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
            
            completion = self.client.chat.completions.create(**params)
            
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
                    
        except Exception as e:
            yield f"Error: {str(e)}"


class LMStudioProvider(BaseProvider):
    """LM Studio provider implementation."""
    
    def get_provider_name(self) -> str:
        return "lmstudio"
    
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
        
        # Validate API base URL format
        api_base = self.config.get('api_base', '')
        if not api_base.startswith(('http://', 'https://')):
            print("api_base must be a valid HTTP URL")
            return False
        
        return True
    
    def test_connection(self) -> bool:
        """Test connection to LM Studio."""
        try:
            client = OpenAI(
                base_url=self.config['api_base'],
                api_key=self.config['api_key']
            )
            
            # Try to list models to test connection
            models = client.models.list()
            return len(models.data) > 0
            
        except Exception as e:
            print(f"LM Studio connection test failed: {e}")
            return False
    
    def create_model_manager(self) -> BaseModelManager:
        """Create LM Studio model manager."""
        client = OpenAI(
            base_url=self.config['api_base'],
            api_key=self.config['api_key']
        )
        return LMStudioModelManager(client)
    
    def create_chat(self) -> BaseChat:
        """Create LM Studio chat."""
        client = OpenAI(
            base_url=self.config['api_base'],
            api_key=self.config['api_key']
        )
        return LMStudioChat(client, self.config)
