"""
Command handlers for RetroChat slash commands.
"""
import os
import re
import sys
from typing import List

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.config_manager import ConfigManager
from core.model_manager import ModelManager
from core.chat import Chat
from core.chat_manager import ChatManager
from utils.terminal_colors import yellow_text

def generate_chat_id():
    """Generate a unique chat ID."""
    chats_dir = 'chats'
    if not os.path.exists(chats_dir):
        os.makedirs(chats_dir)
    existing = set()
    pattern = re.compile(r'^chat_(\d+)$')
    for fname in os.listdir(chats_dir):
        if fname.endswith('.json'):
            base = fname[:-5]
            m = pattern.match(base)
            if m:
                existing.add(int(m.group(1)))
    n = 1
    while n in existing:
        n += 1
    return f'chat_{n}'

class CommandHandlers:
    """Collection of command handler functions."""
    
    def __init__(self, config_manager: ConfigManager, model_manager: ModelManager, 
                 chat: Chat, chat_manager: ChatManager):
        self.config_manager = config_manager
        self.model_manager = model_manager
        self.chat = chat
        self.chat_manager = chat_manager
        self.current_chat = None
        self.history = []
    
    def set_current_chat(self, chat_name: str, history: List):
        """Set the current chat and history."""
        self.current_chat = chat_name
        self.history = history
    
    def cmd_model_list(self):
        """List and select available AI models"""
        models = self.model_manager.get_models()
        if not models:
            print("No models available. Please check your provider configuration.")
            return True
            
        for i, model in enumerate(models):
            model_id = model.get('id', f'model_{i}')
            model_name = model.get('name', model_id)
            print(f"{i}: {model_id}")
            if model_name != model_id:
                print(f"    Name: {model_name}")
            
            # Show additional info for some providers
            if 'description' in model and model['description']:
                print(f"    Description: {model['description'][:100]}...")
            if 'context_length' in model and model['context_length']:
                print(f"    Context Length: {model['context_length']}")
        
        try:
            selection = int(input("Select a model: "))
            if 0 <= selection < len(models):
                selected_model = models[selection]
                self.model_manager.set_default_model(selected_model['id'])
                print(f"Default model set to {selected_model['id']}")
            else:
                print("Invalid selection.")
        except (ValueError, IndexError):
            print("Invalid selection.")
        return True
    
    def cmd_set_stream(self, value):
        """Enable or disable streaming responses (true/false)"""
        try:
            current_provider = self.config_manager.get_current_provider()
            if value.lower() == "true":
                self.config_manager.set_provider_value(current_provider, "stream", True)
                print("Stream enabled.")
            elif value.lower() == "false":
                self.config_manager.set_provider_value(current_provider, "stream", False)
                print("Stream disabled.")
            else:
                print("Invalid value. Use true or false.")
        except Exception:
            print("Invalid command. Use /set stream true/false.")
        return True
    
    def cmd_set_system(self, prompt):
        """Set the system prompt for the AI"""
        try:
            current_provider = self.config_manager.get_current_provider()
            self.config_manager.set_provider_value(current_provider, "system_prompt", prompt)
            print(f"System prompt set to: {prompt}")
        except Exception:
            print("Invalid command. Use /set system <prompt>")
        return True
    
    def cmd_chat_new(self):
        """Start a new chat session"""
        self.current_chat = generate_chat_id()
        self.history = []
        print(f"Started new chat: {self.current_chat}")
        return True
    
    def cmd_chat_save(self, chat_name):
        """Save the current chat with a given name"""
        try:
            if ' ' in chat_name:
                print("Chat name cannot contain spaces.")
            else:
                self.chat_manager.save_chat(chat_name, self.history)
                self.current_chat = chat_name
                print(f"Chat saved as {chat_name}")
        except Exception:
            print("Invalid command. Use /chat save <chat_name>")
        return True
    
    def cmd_chat_load(self, chat_name):
        """Load a previously saved chat"""
        try:
            loaded_history = self.chat_manager.load_chat(chat_name)
            if loaded_history:
                self.history = loaded_history
                self.current_chat = chat_name
                print(f"Chat {chat_name} loaded.")
                print("--- Conversation History ---")
                for msg in self.history:
                    role = msg.get("role", "?")
                    content = msg.get("content", "")
                    if role == "assistant":
                        print(f"[{role}] {yellow_text(content)}")
                    else:
                        print(f"[{role}] {content}")
                print("---------------------------")
            else:
                print("Chat not found.")
        except Exception:
            print("Invalid command. Use /chat load <chat_name>")
        return True
    
    def cmd_chat_delete(self, chat_name):
        """Delete a saved chat"""
        try:
            if self.chat_manager.delete_chat(chat_name):
                print(f"Chat {chat_name} deleted.")
                if self.current_chat == chat_name:
                    self.current_chat = generate_chat_id()
                    self.history = []
            else:
                print("Chat not found.")
        except Exception:
            print("Invalid command. Use /chat delete <chat_name>")
        return True
    
    def cmd_chat_list(self):
        """List all saved chats"""
        chats = self.chat_manager.list_chats()
        if chats:
            print(f"Active chat: {self.current_chat}")
            for chat_name in chats:
                print(chat_name)
        else:
            print("No chats found.")
        return True
    
    def cmd_chat_reset(self):
        """Clear the current chat's conversation history"""
        self.history = []
        print("Current chat history cleared.")
        return True
    
    def cmd_help(self, cmd_registry):
        """Show this help message with all available commands"""
        print("Available commands:")
        print("==================")
        for cmd_name, cmd_info in cmd_registry.get_all_commands().items():
            print(f"{cmd_name:<20} - {cmd_info['description']}")
        return True
    
    def cmd_exit(self):
        """Exit the chat application"""
        return False
    
    def cmd_provider_list(self):
        """List all available and configured providers"""
        available_providers = self.model_manager.get_available_providers()
        configured_providers = self.model_manager.get_configured_providers()
        current_provider = self.model_manager.get_current_provider_name()
        
        print(f"Current provider: {current_provider}")
        print("\nConfigured providers:")
        for provider in configured_providers:
            status = " (current)" if provider == current_provider else ""
            print(f"  {provider}{status}")
        
        print(f"\nAvailable provider types:")
        for provider in available_providers:
            configured = " (configured)" if provider in configured_providers else ""
            print(f"  {provider}{configured}")
        return True
    
    def cmd_provider_switch(self, provider_name):
        """Switch to a different provider"""
        try:
            if self.model_manager.switch_provider(provider_name):
                # Also update chat to use new provider
                self.chat.refresh_provider()
                print(f"Successfully switched to provider: {provider_name}")
            else:
                print(f"Failed to switch to provider: {provider_name}")
        except Exception as e:
            print(f"Error switching provider: {e}")
        return True
    
    def cmd_provider_test(self):
        """Test connection to current provider"""
        try:
            current_provider = self.model_manager.get_current_provider_name()
            if self.model_manager.test_current_provider():
                print(f"✓ Connection to {current_provider} successful")
            else:
                print(f"✗ Connection to {current_provider} failed")
        except Exception as e:
            print(f"Error testing provider: {e}")
        return True
    
    def cmd_provider_config(self, provider_name):
        """Show configuration for a provider"""
        try:
            if provider_name in self.model_manager.get_configured_providers():
                config = self.config_manager.get_provider_config(provider_name)
                print(f"Configuration for {provider_name}:")
                for key, value in config.items():
                    # Hide sensitive values
                    if 'key' in key.lower() or 'secret' in key.lower():
                        display_value = '*' * len(str(value)) if value else 'not set'
                    else:
                        display_value = value
                    print(f"  {key}: {display_value}")
            else:
                print(f"Provider {provider_name} is not configured")
        except Exception as e:
            print(f"Error showing provider config: {e}")
        return True
