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
    # Initialize core components
    config_manager = ConfigManager()
    model_manager = ModelManager(config_manager)
    chat = Chat(config_manager)
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
    
    # Load the last used chat or create a new one
    existing_chats = chat_manager.list_chats()
    if existing_chats:
        # Load the most recent chat (first in the sorted list)
        current_chat = existing_chats[0]
        history = chat_manager.load_chat(current_chat) or []
        print(f"Loaded last used chat: {current_chat}")
        if history:
            print("--- Recent Conversation ---")
            # Show last few messages for context
            recent_messages = history[-4:] if len(history) > 4 else history
            for msg in recent_messages:
                role = msg.get("role", "?")
                content = msg.get("content", "")
                if role == "assistant":
                    print(f"[{role}] {yellow_text(content[:100])}{'...' if len(content) > 100 else ''}")
                else:
                    print(f"[{role}] {content[:100]}{'...' if len(content) > 100 else ''}")
            print("---------------------------")
    else:
        # No existing chats, create a new one
        current_chat = generate_chat_id()
        history = []
        print("Starting with a new chat session")
    
    # Set the current chat in command handlers
    cmd_handlers.set_current_chat(current_chat, history)
    
    print()
    
    # Register all commands
    cmd_registry.register("/model list", "List and select available AI models", cmd_handlers.cmd_model_list)
    cmd_registry.register("/set stream", "Enable or disable streaming responses (true/false)", cmd_handlers.cmd_set_stream)
    cmd_registry.register("/set system", "Set the system prompt for the AI", cmd_handlers.cmd_set_system)
    cmd_registry.register("/provider list", "List all available and configured providers", cmd_handlers.cmd_provider_list)
    cmd_registry.register("/provider switch", "Switch to a different provider", cmd_handlers.cmd_provider_switch)
    cmd_registry.register("/provider test", "Test connection to current provider", cmd_handlers.cmd_provider_test)
    cmd_registry.register("/provider config", "Show configuration for a provider", cmd_handlers.cmd_provider_config)
    cmd_registry.register("/chat new", "Start a new chat session", cmd_handlers.cmd_chat_new)
    cmd_registry.register("/chat save", "Save the current chat with a given name", cmd_handlers.cmd_chat_save)
    cmd_registry.register("/chat load", "Load a previously saved chat", cmd_handlers.cmd_chat_load)
    cmd_registry.register("/chat delete", "Delete a saved chat", cmd_handlers.cmd_chat_delete)
    cmd_registry.register("/chat reset", "Clear the current chat's conversation history", cmd_handlers.cmd_chat_reset)
    cmd_registry.register("/chat list", "List all saved chats", cmd_handlers.cmd_chat_list)
    cmd_registry.register("/help", "Show this help message with all available commands", lambda: cmd_handlers.cmd_help(cmd_registry))
    cmd_registry.register("/exit", "Exit the chat application", cmd_handlers.cmd_exit)

    # Main application loop
    while True:
        user_input = input("> ")
        
        # Check if input is a command (starts with /)
        if user_input.startswith("/"):
            command_handled = False
            
            # Parse and execute commands
            if user_input.strip() == "/model list":
                cmd_registry.execute_command("/model list")
                command_handled = True
            elif user_input.startswith("/set stream "):
                try:
                    value = user_input.split(" ", 2)[2]
                    cmd_registry.execute_command("/set stream", value)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /set stream true/false.")
                    command_handled = True
            elif user_input.startswith("/set system "):
                try:
                    value = user_input.split(" ", 2)[2]
                    cmd_registry.execute_command("/set system", value)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /set system <prompt>")
                    command_handled = True
            elif user_input.strip() == "/chat new":
                cmd_registry.execute_command("/chat new")
                command_handled = True
            elif user_input.startswith("/chat save "):
                try:
                    chat_name = user_input.split(" ", 2)[2]
                    cmd_registry.execute_command("/chat save", chat_name)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /chat save <chat_name>")
                    command_handled = True
            elif user_input.startswith("/chat load "):
                try:
                    chat_name = user_input.split(" ", 2)[2]
                    cmd_registry.execute_command("/chat load", chat_name)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /chat load <chat_name>")
                    command_handled = True
            elif user_input.startswith("/chat delete "):
                try:
                    chat_name = user_input.split(" ", 2)[2]
                    cmd_registry.execute_command("/chat delete", chat_name)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /chat delete <chat_name>")
                    command_handled = True
            elif user_input.strip() == "/chat reset":
                cmd_registry.execute_command("/chat reset")
                command_handled = True
            elif user_input.strip() == "/chat list":
                cmd_registry.execute_command("/chat list")
                command_handled = True
            elif user_input.strip() == "/help":
                cmd_registry.execute_command("/help")
                command_handled = True
            elif user_input.strip() == "/provider list":
                cmd_registry.execute_command("/provider list")
                command_handled = True
            elif user_input.startswith("/provider switch "):
                try:
                    provider_name = user_input.split(" ", 2)[2]
                    cmd_registry.execute_command("/provider switch", provider_name)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /provider switch <provider_name>")
                    command_handled = True
            elif user_input.strip() == "/provider test":
                cmd_registry.execute_command("/provider test")
                command_handled = True
            elif user_input.startswith("/provider config "):
                try:
                    provider_name = user_input.split(" ", 2)[2]
                    cmd_registry.execute_command("/provider config", provider_name)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /provider config <provider_name>")
                    command_handled = True
            elif user_input.strip() == "/exit":
                if not cmd_registry.execute_command("/exit"):
                    break
                command_handled = True
            
            # If command wasn't handled, show error
            if not command_handled:
                print(f"Command '{user_input}' does not exist. Type /help to see available commands.")
        else:
            # Regular message, send to AI
            chat.send_message(user_input, cmd_handlers.history)
            chat_manager.save_chat(cmd_handlers.current_chat, cmd_handlers.history)


if __name__ == "__main__":
    main()
