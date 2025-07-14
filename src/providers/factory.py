"""
Provider factory for automatically discovering and creating chat providers
"""
import importlib
import pkgutil
from typing import Dict, Type, Optional, Any
from pathlib import Path

from . import ChatProvider


class ProviderFactory:
    """Factory for creating chat providers"""
    
    def __init__(self):
        self._providers: Dict[str, Type[ChatProvider]] = {}
        self._discover_providers()
    
    def _discover_providers(self):
        """Automatically discover provider classes"""
        providers_dir = Path(__file__).parent
        
        # Import all modules in the providers directory
        for importer, modname, ispkg in pkgutil.iter_modules([str(providers_dir)]):
            if modname.startswith('_'):  # Skip private modules
                continue
                
            try:
                module = importlib.import_module(f'.{modname}', package=__package__)
                
                # Find provider classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # Check if it's a provider class (but not the base class)
                    if (isinstance(attr, type) and 
                        issubclass(attr, ChatProvider) and 
                        attr is not ChatProvider):
                        
                        provider_name = getattr(attr, 'name', None)
                        if isinstance(provider_name, property):
                            # If it's a property, create an instance to get the name
                            try:
                                temp_instance = attr({})
                                provider_name = temp_instance.name
                            except:
                                provider_name = attr.__name__.lower().replace('provider', '')
                        elif not isinstance(provider_name, str):
                            provider_name = attr.__name__.lower().replace('provider', '')
                        
                        self._providers[provider_name] = attr
                        
            except ImportError as e:
                print(f"Warning: Could not import provider module {modname}: {e}")
    
    def create_provider(self, provider_name: str, config: Dict[str, Any]) -> ChatProvider:
        """Create a provider instance"""
        if provider_name not in self._providers:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(self._providers.keys())}")
        
        provider_class = self._providers[provider_name]
        return provider_class(config)
    
    def list_providers(self) -> Dict[str, Type[ChatProvider]]:
        """Get all available providers"""
        return self._providers.copy()
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Check which providers are available (can connect)"""
        available = {}
        
        for name, provider_class in self._providers.items():
            try:
                # Create a provider with minimal config to test availability
                provider = provider_class({})
                available[name] = provider.is_available()
            except Exception:
                available[name] = False
        
        return available


# Global instance
_factory = ProviderFactory()


def get_provider(provider_name: str, config: Dict[str, Any]) -> ChatProvider:
    """Get a provider instance"""
    return _factory.create_provider(provider_name, config)


def list_available_providers() -> Dict[str, bool]:
    """List all available providers and their availability status"""
    return _factory.get_available_providers()
