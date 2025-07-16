from typing import List, Dict, Any
from .config_manager import ConfigManager
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from providers import provider_factory
from utils.terminal_colors import yellow_text


class Chat:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._current_provider = None
        self._chat = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the current provider and its chat interface."""
        current_provider_name = self.config_manager.get_current_provider()
        provider_config = self.config_manager.get_current_provider_config()
        
        # Create provider instance
        self._current_provider = provider_factory.create_provider(
            current_provider_name, 
            provider_config
        )
        
        if self._current_provider:
            self._chat = self._current_provider.create_chat()
            provider_factory.set_current_provider(self._current_provider)
        else:
            print(f"Failed to initialize provider: {current_provider_name}")

    def refresh_provider(self):
        """Refresh the current provider (useful after config changes)."""
        self._initialize_provider()

    def send_message(self, message: str, history: List[Dict[str, Any]]) -> str:
        """Send a message and get a response."""
        if not self._chat:
            print("No chat interface available. Please check provider configuration.")
            return "Error: No chat interface available"

        # Get current provider config for streaming setting
        current_provider = self.config_manager.get_current_provider()
        provider_config = self.config_manager.get_provider_config(current_provider)
        is_streaming = provider_config.get('stream', False)

        # Check if default model is set
        default_model = provider_config.get('default_model')
        if not default_model:
            return "No default model selected. Please use /model list to select one."

        try:
            if is_streaming:
                # Handle streaming response
                response = ''
                for chunk in self._chat.send_message_stream(message, history):
                    print(yellow_text(chunk), end='', flush=True)
                    response += chunk
                print()  # New line after streaming
                
                # Add messages to history
                if not any(msg.get('role') == 'system' for msg in history):
                    system_prompt = provider_config.get('system_prompt')
                    if system_prompt:
                        history.append({"role": "system", "content": system_prompt})
                
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return response
            else:
                # Handle non-streaming response
                response = self._chat.send_message(message, history)
                print(yellow_text(response))
                
                # Add messages to history
                if not any(msg.get('role') == 'system' for msg in history):
                    system_prompt = provider_config.get('system_prompt')
                    if system_prompt:
                        history.append({"role": "system", "content": system_prompt})
                
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return response
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

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
