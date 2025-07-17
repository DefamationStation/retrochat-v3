"""
RetroChat v3 - Multi-Provider AI Chat Application

Main entry point for the application.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.core.model_manager import ModelManager
from src.core.chat import Chat
from src.core.chat_manager import ChatManager
from src.ui.command_registry import CommandRegistry
from src.ui.commands import CommandHandlers, generate_chat_id
from src.utils.terminal_colors import yellow_text


def main():
    """Main application entry point."""
    try:
        # Initialize core components
        print("Initializing configuration manager...")
        config_manager = ConfigManager()
        
        print("Initializing model manager...")
        model_manager = ModelManager(config_manager)
        
        print("Initializing chat...")
        chat = Chat(config_manager)
        
        print("Initializing chat manager...")
        chat_manager = ChatManager()
        
        # Initialize UI components
        cmd_registry = CommandRegistry()
        cmd_handlers = CommandHandlers(config_manager, model_manager, chat, chat_manager)
        
        # Display welcome message
        current_provider = model_manager.get_current_provider_name()
        current_model = model_manager.get_default_model() or "No model selected"
        
        print("=" * 50)
        print("🎉 Welcome to RetroChat! 🎉")
        print("=" * 50)
        print(f"Current Provider: {current_provider}")
        print(f"Current Model: {current_model}")
        print("Type /help for available commands")
        print("=" * 50)
    except Exception as e:
        print(f"Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Load the last used chat or create a new one
    existing_chats = chat_manager.list_chats()
    if existing_chats:
        # Load the most recent chat (first in the sorted list)
        current_chat = existing_chats[0]
        history = chat_manager.load_chat(current_chat) or []
        print(f"Loaded last used chat: {current_chat}")
        if history:
            # Show recent messages for context  
            from src.ui.commands import display_chat_history
            display_chat_history(history, show_all=False, max_recent=6)
    else:
        # No existing chats, create a new one
        current_chat = generate_chat_id()
        history = []
        print("Starting with a new chat session")
    
    # Set the current chat in command handlers
    cmd_handlers.set_current_chat(current_chat, history)
    
    print()
    
    # Register all commands
    cmd_registry.register("/model", "Usage: /model list", cmd_handlers.cmd_model_list, takes_args=True)
    cmd_registry.register("/set", "Usage: /set stream true/false or /set system <prompt>", cmd_handlers.cmd_set, takes_args=True)
    cmd_registry.register("/provider", "Usage: /provider list, switch, test, config", cmd_handlers.cmd_provider, takes_args=True)
    cmd_registry.register("/chat", "Usage: /chat new, save, load, delete, reset, list", cmd_handlers.cmd_chat, takes_args=True)
    cmd_registry.register("/help", "Show this help message with all available commands", lambda: cmd_handlers.cmd_help(cmd_registry))
    cmd_registry.register("/exit", "Exit the chat application", cmd_handlers.cmd_exit)

    # Main application loop
    while True:
        user_input = input("> ")
        
        if not user_input.startswith("/"):
            chat.send_message(user_input, cmd_handlers.history)
            chat_manager.save_chat(cmd_handlers.current_chat, cmd_handlers.history)
            continue

        parts = user_input.strip().split(" ")
        command_name = parts[0]
        args = parts[1:]

        command = cmd_registry.get_command(command_name)

        if command:
            try:
                if command_name == "/exit":
                    if not cmd_registry.execute_command(command_name, *args):
                        break
                else:
                    cmd_registry.execute_command(command_name, *args)
            except Exception as e:
                print(f"Error executing command: {e}")
        else:
            print(f"Command '{command_name}' does not exist. Type /help to see available commands.")


if __name__ == "__main__":
    main()
