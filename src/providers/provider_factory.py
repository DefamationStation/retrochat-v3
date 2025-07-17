"""
Provider discovery and management system.

This module handles automatic discovery of provider implementations
and provides a factory for creating provider instances.
"""

import os
import sys
import importlib
import inspect
from typing import Dict, List, Type, Optional, Any
from .base_provider import BaseProvider


class ProviderRegistry:
    """Registry for managing available providers."""
    
    def __init__(self):
        self._providers: Dict[str, Type[BaseProvider]] = {}
        self._discover_providers()
    
    def _discover_providers(self):
        """Automatically discover provider implementations."""
        # Check if we're running in a PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle - manually import known providers
            self._register_bundled_providers()
        else:
            # Running normally - discover from filesystem
            self._discover_filesystem_providers()
    
    def _register_bundled_providers(self):
        """Register providers when running in PyInstaller bundle."""
        # Manually import known provider modules
        known_providers = ['lmstudio_provider', 'openrouter_provider']
        
        for module_name in known_providers:
            try:
                # Try different import paths for PyInstaller
                module = None
                import_paths = [
                    f'src.providers.{module_name}',
                    f'providers.{module_name}',
                    module_name
                ]
                
                for import_path in import_paths:
                    try:
                        module = importlib.import_module(import_path)
                        break
                    except ImportError:
                        continue
                
                if not module:
                    continue
                
                # Look for classes that inherit from BaseProvider
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseProvider) and 
                        obj != BaseProvider and 
                        hasattr(obj, 'get_provider_name')):
                        
                        # Create a temporary instance to get the provider name
                        try:
                            temp_instance = obj({})
                            provider_name = temp_instance.get_provider_name()
                            self._providers[provider_name] = obj
                        except Exception as e:
                            print(f"Error registering provider in {module_name}: {e}")
                            
            except Exception as e:
                print(f"Error processing provider module {module_name}: {e}")
    
    def _discover_filesystem_providers(self):
        """Discover providers from filesystem (normal execution)."""
        providers_dir = os.path.dirname(__file__)
        
        # Look for Python files in the providers directory
        for filename in os.listdir(providers_dir):
            if filename.endswith('.py') and not filename.startswith('_') and filename not in ['base_provider.py', 'base_openai_provider.py']:
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module = importlib.import_module(f'providers.{module_name}')
                    
                    # Look for classes that inherit from BaseProvider
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseProvider) and 
                            obj != BaseProvider and 
                            hasattr(obj, 'get_provider_name')):
                            
                            # Create a temporary instance to get the provider name
                            try:
                                temp_instance = obj({})
                                provider_name = temp_instance.get_provider_name()
                                self._providers[provider_name] = obj
                            except Exception as e:
                                print(f"Error discovering provider in {module_name}: {e}")
                                
                except ImportError as e:
                    print(f"Could not import provider module {module_name}: {e}")
                except Exception as e:
                    print(f"Error processing provider module {module_name}: {e}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self._providers.keys())
    
    def get_provider_class(self, provider_name: str) -> Optional[Type[BaseProvider]]:
        """Get provider class by name."""
        return self._providers.get(provider_name)
    
    def create_provider(self, provider_name: str, config: Dict[str, Any]) -> Optional[BaseProvider]:
        """Create a provider instance with the given configuration."""
        provider_class = self.get_provider_class(provider_name)
        if provider_class:
            try:
                return provider_class(config)
            except Exception as e:
                print(f"Error creating provider {provider_name}: {e}")
                return None
        return None
    
    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a provider."""
        provider_class = self.get_provider_class(provider_name)
        if provider_class:
            try:
                temp_instance = provider_class({})
                return {
                    'name': provider_name,
                    'required_config': temp_instance.get_required_config_keys(),
                    'optional_config': temp_instance.get_optional_config_keys(),
                    'class': provider_class.__name__
                }
            except Exception as e:
                print(f"Error getting provider info for {provider_name}: {e}")
        return None


class ProviderFactory:
    """Factory for creating and managing provider instances."""
    
    def __init__(self):
        self.registry = ProviderRegistry()
        self._current_provider: Optional[BaseProvider] = None
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return self.registry.get_available_providers()
    
    def create_provider(self, provider_name: str, config: Dict[str, Any]) -> Optional[BaseProvider]:
        """Create and validate a provider instance."""
        provider = self.registry.create_provider(provider_name, config)
        if provider and provider.validate_config():
            return provider
        return None
    
    def set_current_provider(self, provider: BaseProvider):
        """Set the current active provider."""
        self._current_provider = provider
    
    def get_current_provider(self) -> Optional[BaseProvider]:
        """Get the current active provider."""
        return self._current_provider
    
    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific provider."""
        return self.registry.get_provider_info(provider_name)
    
    def list_all_providers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available providers."""
        info = {}
        for provider_name in self.get_available_providers():
            provider_info = self.get_provider_info(provider_name)
            if provider_info:
                info[provider_name] = provider_info
        return info


# Global factory instance
provider_factory = ProviderFactory()
