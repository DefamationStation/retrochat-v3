"""
Base provider interface for AI providers.

This module defines the abstract interfaces that all AI providers must implement
to be compatible with the retrochat application.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator


class BaseModelManager(ABC):
    """Abstract base class for model management operations."""
    
    @abstractmethod
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Retrieve available models from the provider.
        
        Returns:
            List of model dictionaries with at least 'id' and 'name' fields
        """
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_id: The ID of the model to get info for
            
        Returns:
            Dictionary containing model information
        """
        pass


class BaseChat(ABC):
    """Abstract base class for chat operations."""
    
    @abstractmethod
    def send_message(self, message: str, history: List[Dict[str, Any]], **kwargs) -> str:
        """
        Send a message and get a response.
        
        Args:
            message: The user message to send
            history: Conversation history as list of message dictionaries
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The assistant's response as a string
        """
        pass
    
    @abstractmethod
    def send_message_stream(self, message: str, history: List[Dict[str, Any]], **kwargs) -> Iterator[str]:
        """
        Send a message and get a streaming response.
        
        Args:
            message: The user message to send
            history: Conversation history as list of message dictionaries
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Yields:
            Response chunks as strings
        """
        pass


class BaseProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider configuration dictionary
        """
        self.config = config
        self.name = self.get_provider_name()
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this provider.
        
        Returns:
            String name of the provider
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate that the provider configuration is correct.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_required_config_keys(self) -> List[str]:
        """
        Get the list of required configuration keys for this provider.
        
        Returns:
            List of required configuration key names
        """
        pass
    
    @abstractmethod
    def get_optional_config_keys(self) -> List[str]:
        """
        Get the list of optional configuration keys for this provider.
        
        Returns:
            List of optional configuration key names
        """
        pass
    
    @abstractmethod
    def create_model_manager(self) -> BaseModelManager:
        """
        Create a model manager instance for this provider.
        
        Returns:
            BaseModelManager implementation for this provider
        """
        pass
    
    @abstractmethod
    def create_chat(self) -> BaseChat:
        """
        Create a chat instance for this provider.
        
        Returns:
            BaseChat implementation for this provider
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the provider can be reached with current configuration.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
