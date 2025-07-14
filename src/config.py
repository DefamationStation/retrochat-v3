"""
Configuration management for the chat application
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field


@dataclass
class ProviderConfig:
    """Base configuration for a provider"""
    host: str = "localhost"
    port: int = 1234
    model: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 30
    base_url: Optional[str] = None  # For custom base URLs
    use_openai_format: bool = True  # Use OpenAI-compatible API


@dataclass
class ChatConfig:
    """Configuration for chat behavior"""
    system_prompt: str = "You are a helpful AI assistant."
    max_tokens: int = 8000
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 40
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    repeat_penalty: float = 1.1
    stream: bool = True
    stop_sequences: Optional[List[str]] = field(default_factory=lambda: None)
    seed: Optional[int] = None
    show_thinking: bool = False  # Whether to show reasoning thinking tags


@dataclass
class AppConfig:
    """Main application configuration"""
    default_provider: str = "lmstudio"
    providers: Optional[Dict[str, ProviderConfig]] = None
    chat: Optional[ChatConfig] = None
    
    def __post_init__(self):
        if self.providers is None:
            self.providers = {"lmstudio": ProviderConfig()}
        if self.chat is None:
            self.chat = ChatConfig()


class ConfigManager:
    """Manages configuration loading and saving"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = self._find_config_file()
        self.config_path = Path(config_path)
        self._config: Optional[AppConfig] = None
    
    def _find_config_file(self) -> str:
        """Find configuration file in current directory or home directory"""
        candidates = [
            Path.cwd() / "config.json",
            Path.home() / ".retrochat" / "config.json",
            Path.cwd() / ".retrochat.json"
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        # Default to current directory
        return str(Path.cwd() / "config.json")
    
    def load_config(self) -> AppConfig:
        """Load configuration from file"""
        if self._config is not None:
            return self._config
            
        if not self.config_path.exists():
            self._config = AppConfig()
            self.save_config()
            return self._config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle legacy config format
            if "lm_studio_host" in data:
                self._config = self._migrate_legacy_config(data)
            else:
                self._config = self._parse_new_config(data)
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            self._config = AppConfig()
        
        return self._config
    
    def _migrate_legacy_config(self, data: Dict[str, Any]) -> AppConfig:
        """Migrate from legacy config format"""
        provider_config = ProviderConfig(
            host=data.get("lm_studio_host", "localhost"),
            port=data.get("lm_studio_port", 1234),
            model=data.get("default_model")
        )
        
        chat_config = ChatConfig(
            system_prompt=data.get("system_prompt", "You are a helpful AI assistant."),
            max_tokens=data.get("max_tokens", 8000),
            temperature=data.get("temperature", 0.7)
        )
        
        return AppConfig(
            default_provider="lmstudio",
            providers={"lmstudio": provider_config},
            chat=chat_config
        )
    
    def _parse_new_config(self, data: Dict[str, Any]) -> AppConfig:
        """Parse new config format"""
        providers = {}
        if "providers" in data:
            for name, provider_data in data["providers"].items():
                providers[name] = ProviderConfig(**provider_data)
        else:
            providers["lmstudio"] = ProviderConfig()
        
        chat_config = ChatConfig()
        if "chat" in data:
            chat_config = ChatConfig(**data["chat"])
        
        return AppConfig(
            default_provider=data.get("default_provider", "lmstudio"),
            providers=providers,
            chat=chat_config
        )
    
    def save_config(self) -> None:
        """Save configuration to file"""
        if self._config is None:
            return
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict format
        config_dict = {
            "default_provider": self._config.default_provider,
            "providers": {
                name: asdict(provider) 
                for name, provider in (self._config.providers or {}).items()
            },
            "chat": asdict(self._config.chat or ChatConfig())
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
    
    def get_provider_config(self, provider_name: Optional[str] = None) -> ProviderConfig:
        """Get configuration for a specific provider"""
        config = self.load_config()
        
        if provider_name is None:
            provider_name = config.default_provider
        
        providers = config.providers or {}
        if provider_name not in providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return providers[provider_name]
    
    def get_chat_config(self) -> ChatConfig:
        """Get chat configuration"""
        return self.load_config().chat or ChatConfig()
    
    def list_providers(self) -> Dict[str, ProviderConfig]:
        """Get all available providers"""
        return self.load_config().providers or {}
