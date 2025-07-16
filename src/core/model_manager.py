from typing import List, Dict, Any, Optional
from .config_manager import ConfigManager
import sys
import os

# Import provider factory with proper path handling
try:
    from src.providers import provider_factory
except ImportError:
    try:
        from providers import provider_factory
    except ImportError:
        # Last resort - add to path and try again
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from providers import provider_factory

class ModelManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._current_provider = None
        self._model_manager = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the current provider and its model manager."""
        current_provider_name = self.config_manager.get_current_provider()
        provider_config = self.config_manager.get_current_provider_config()
        
        # Create provider instance
        self._current_provider = provider_factory.create_provider(
            current_provider_name, 
            provider_config
        )
        
        if self._current_provider:
            self._model_manager = self._current_provider.create_model_manager()
            provider_factory.set_current_provider(self._current_provider)
        else:
            print(f"Failed to initialize provider: {current_provider_name}")

    def refresh_provider(self):
        """Refresh the current provider (useful after config changes)."""
        self._initialize_provider()

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from the current provider."""
        if not self._model_manager:
            print("No model manager available. Please check provider configuration.")
            return []
        
        try:
            models = self._model_manager.get_models()
            return models
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        if not self._model_manager:
            return {}
        
        try:
            return self._model_manager.get_model_info(model_id)
        except Exception as e:
            print(f"Error fetching model info: {e}")
            return {}

    def set_default_model(self, model_id: str):
        """Set the default model for the current provider."""
        current_provider = self.config_manager.get_current_provider()
        self.config_manager.set_provider_value(current_provider, 'default_model', model_id)

    def get_default_model(self) -> Optional[str]:
        """Get the default model for the current provider."""
        current_provider = self.config_manager.get_current_provider()
        return self.config_manager.get_provider_value(current_provider, 'default_model')

    def get_current_provider_name(self) -> str:
        """Get the name of the current provider."""
        return self.config_manager.get_current_provider()

    def switch_provider(self, provider_name: str) -> bool:
        """Switch to a different provider."""
        if provider_name not in self.config_manager.list_configured_providers():
            print(f"Provider '{provider_name}' is not configured.")
            return False
        
        # Test the provider configuration
        provider_config = self.config_manager.get_provider_config(provider_name)
        test_provider = provider_factory.create_provider(provider_name, provider_config)
        
        if not test_provider or not test_provider.test_connection():
            print(f"Failed to connect to provider '{provider_name}'. Please check configuration.")
            return False
        
        # Switch to the new provider
        self.config_manager.set_current_provider(provider_name)
        self._initialize_provider()
        print(f"Switched to provider: {provider_name}")
        return True

    def test_current_provider(self) -> bool:
        """Test connection to the current provider."""
        if not self._current_provider:
            return False
        
        return self._current_provider.test_connection()

    def get_available_providers(self) -> List[str]:
        """Get list of all available provider types."""
        return provider_factory.get_available_providers()

    def get_configured_providers(self) -> List[str]:
        """Get list of configured providers."""
        return self.config_manager.list_configured_providers()
