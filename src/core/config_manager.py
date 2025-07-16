import json
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.config = self.load_config()
        self._migrate_legacy_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure."""
        return {
            "current_provider": "lmstudio",
            "providers": {
                "lmstudio": {
                    "api_base": "http://localhost:1234/v1",
                    "api_key": "lm-studio",
                    "default_model": "",
                    "stream": True,
                    "system_prompt": "You're an intelligent AI assistant."
                }
            }
        }

    def _migrate_legacy_config(self):
        """Migrate legacy flat configuration to new provider-based structure."""
        # Check if this is a legacy config (has api_base but no providers structure)
        if 'api_base' in self.config and 'providers' not in self.config:
            print("Migrating legacy configuration...")
            
            # Create new structure
            legacy_config = self.config.copy()
            self.config = self._get_default_config()
            
            # Migrate LM Studio settings
            lmstudio_config = self.config['providers']['lmstudio']
            
            if 'api_base' in legacy_config:
                lmstudio_config['api_base'] = legacy_config['api_base']
            if 'api_key' in legacy_config:
                lmstudio_config['api_key'] = legacy_config['api_key']
            if 'default_model' in legacy_config:
                lmstudio_config['default_model'] = legacy_config['default_model']
            if 'stream' in legacy_config:
                lmstudio_config['stream'] = legacy_config['stream']
            if 'system_prompt' in legacy_config:
                lmstudio_config['system_prompt'] = legacy_config['system_prompt']
            
            # Save migrated config
            self.save_config()
            print("Configuration migrated successfully!")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self.config[key] = value
        self.save_config()

    def get_current_provider(self) -> str:
        """Get the name of the current provider."""
        return self.config.get('current_provider', 'lmstudio')

    def set_current_provider(self, provider_name: str):
        """Set the current provider."""
        self.config['current_provider'] = provider_name
        self.save_config()

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        return self.config.get('providers', {}).get(provider_name, {})

    def set_provider_config(self, provider_name: str, provider_config: Dict[str, Any]):
        """Set configuration for a specific provider."""
        if 'providers' not in self.config:
            self.config['providers'] = {}
        self.config['providers'][provider_name] = provider_config
        self.save_config()

    def update_provider_config(self, provider_name: str, updates: Dict[str, Any]):
        """Update specific keys in a provider's configuration."""
        if 'providers' not in self.config:
            self.config['providers'] = {}
        if provider_name not in self.config['providers']:
            self.config['providers'][provider_name] = {}
        
        self.config['providers'][provider_name].update(updates)
        self.save_config()

    def get_provider_value(self, provider_name: str, key: str, default: Any = None) -> Any:
        """Get a specific value from a provider's configuration."""
        provider_config = self.get_provider_config(provider_name)
        return provider_config.get(key, default)

    def set_provider_value(self, provider_name: str, key: str, value: Any):
        """Set a specific value in a provider's configuration."""
        self.update_provider_config(provider_name, {key: value})

    def get_current_provider_config(self) -> Dict[str, Any]:
        """Get configuration for the current provider."""
        current_provider = self.get_current_provider()
        return self.get_provider_config(current_provider)

    def list_configured_providers(self) -> list:
        """Get list of configured provider names."""
        return list(self.config.get('providers', {}).keys())

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
