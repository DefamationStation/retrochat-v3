"""
Base provider for OpenAI-compatible APIs.

This module provides a base implementation for providers that are compatible
with the OpenAI API, such as LM Studio and OpenRouter. It abstracts away the
common logic for model management and chat operations.
"""

from abc import abstractmethod
from typing import List, Dict, Any, Iterator
from openai import OpenAI
from .base_provider import BaseProvider, BaseModelManager, BaseChat


class BaseOpenAIModelManager(BaseModelManager):
    """Base model manager for OpenAI-compatible APIs."""

    def __init__(self, client: OpenAI):
        self.client = client

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from the provider."""
        try:
            models_response = self.client.models.list()
            models = []
            for model in models_response.data:
                models.append({
                    'id': model.id,
                    'name': model.id,
                    'object': getattr(model, 'object', 'model'),
                    'created': getattr(model, 'created', None),
                    'owned_by': getattr(model, 'owned_by', 'unknown'),
                })
            return models
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        models = self.get_models()
        for model in models:
            if model['id'] == model_id:
                return model
        return {}


class BaseOpenAIChat(BaseChat):
    """Base chat implementation for OpenAI-compatible APIs."""

    def __init__(self, client: OpenAI, config: Dict[str, Any]):
        self.client = client
        self.config = config

    def _prepare_messages(self, message: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare the list of messages for the API call."""
        messages = history.copy()

        if not any(msg.get('role') == 'system' for msg in messages):
            system_prompt = self.config.get('system_prompt')
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": message})
        return messages

    def _prepare_params(self, messages: List[Dict[str, Any]], stream: bool, **kwargs) -> Dict[str, Any]:
        """Prepare the parameters for the API call."""
        model = self.config.get('default_model')
        if not model:
            raise ValueError("No default model configured")

        params = {
            'model': model,
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'stream': stream
        }

        if 'max_tokens' in kwargs:
            params['max_tokens'] = kwargs['max_tokens']
        if 'top_p' in kwargs:
            params['top_p'] = kwargs['top_p']

        return params

    def send_message(self, message: str, history: List[Dict[str, Any]], **kwargs) -> str:
        """Send a message and get a response."""
        try:
            messages = self._prepare_messages(message, history)
            params = self._prepare_params(messages, stream=False, **kwargs)

            completion = self.client.chat.completions.create(**params)
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def send_message_stream(self, message: str, history: List[Dict[str, Any]], **kwargs) -> Iterator[str]:
        """Send a message and get a streaming response."""
        try:
            messages = self._prepare_messages(message, history)
            params = self._prepare_params(messages, stream=True, **kwargs)

            completion = self.client.chat.completions.create(**params)

            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"Error: {str(e)}"


class BaseOpenAIProvider(BaseProvider):
    """Base provider for OpenAI-compatible APIs."""

    @abstractmethod
    def get_api_base(self) -> str:
        """Get the API base URL for the provider."""
        pass

    def get_client(self) -> OpenAI:
        """Get an OpenAI client instance."""
        return OpenAI(
            base_url=self.get_api_base(),
            api_key=self.config.get('api_key')
        )

    def create_model_manager(self) -> BaseModelManager:
        """Create a model manager instance."""
        return BaseOpenAIModelManager(self.get_client())

    def create_chat(self) -> BaseChat:
        """Create a chat instance."""
        return BaseOpenAIChat(self.get_client(), self.config)

    def test_connection(self) -> bool:
        """Test connection to the provider."""
        try:
            client = self.get_client()
            client.models.list()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
