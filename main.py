import random
import string
from config_manager import ConfigManager
from model_manager import ModelManager
from chat import Chat
from chat_manager import ChatManager

def generate_chat_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

class CommandRegistry:
    """Registry for managing slash commands with descriptions"""
    def __init__(self):
        self.commands = {}
    
    def register(self, command, description, handler):
        """Register a command with its description and handler function"""
        self.commands[command] = {
            'description': description,
            'handler': handler
        }
    
    def get_command(self, command):
        """Get command info by name"""
        return self.commands.get(command)
    
    def get_all_commands(self):
        """Get all registered commands"""
        return self.commands
    
    def execute_command(self, command, *args):
        """Execute a command if it exists"""
        cmd_info = self.get_command(command)
        if cmd_info:
            return cmd_info['handler'](*args)
        return False

def main():
    config_manager = ConfigManager()
    model_manager = ModelManager(config_manager)
    chat = Chat(config_manager)
    chat_manager = ChatManager()
    current_chat = generate_chat_id()
    history = []
    
    # Create command registry
    cmd_registry = CommandRegistry()
    
    # Command handler functions
    def cmd_list_models():
        """List and select available AI models"""
        models = model_manager.get_models()
        for i, model in enumerate(models.data):
            print(f"{i}: {model.id}")
        try:
            selection = int(input("Select a model: "))
            model_manager.set_default_model(models.data[selection].id)
            print(f"Default model set to {models.data[selection].id}")
        except (ValueError, IndexError):
            print("Invalid selection.")
        return True
    
    def cmd_set_stream(value):
        """Enable or disable streaming responses (true/false)"""
        try:
            if value.lower() == "true":
                config_manager.set("stream", True)
                print("Stream enabled.")
            elif value.lower() == "false":
                config_manager.set("stream", False)
                print("Stream disabled.")
            else:
                print("Invalid value. Use true or false.")
        except Exception:
            print("Invalid command. Use /set stream true/false.")
        return True
    
    def cmd_set_system(prompt):
        """Set the system prompt for the AI"""
        try:
            config_manager.set("system_prompt", prompt)
            print(f"System prompt set to: {prompt}")
        except Exception:
            print("Invalid command. Use /set system <prompt>")
        return True
    
    def cmd_new():
        """Start a new chat session"""
        nonlocal current_chat, history
        current_chat = generate_chat_id()
        history = []
        print(f"Started new chat: {current_chat}")
        return True
    
    def cmd_save(chat_name):
        """Save the current chat with a given name"""
        nonlocal current_chat
        try:
            if ' ' in chat_name:
                print("Chat name cannot contain spaces.")
            else:
                chat_manager.save_chat(chat_name, history)
                current_chat = chat_name
                print(f"Chat saved as {chat_name}")
        except Exception:
            print("Invalid command. Use /save <chat_name>")
        return True
    
    def cmd_load(chat_name):
        """Load a previously saved chat"""
        nonlocal current_chat, history
        try:
            loaded_history = chat_manager.load_chat(chat_name)
            if loaded_history:
                history = loaded_history
                current_chat = chat_name
                print(f"Chat {chat_name} loaded.")
            else:
                print("Chat not found.")
        except Exception:
            print("Invalid command. Use /load <chat_name>")
        return True
    
    def cmd_delete(chat_name):
        """Delete a saved chat"""
        nonlocal current_chat, history
        try:
            if chat_manager.delete_chat(chat_name):
                print(f"Chat {chat_name} deleted.")
                if current_chat == chat_name:
                    current_chat = generate_chat_id()
                    history = []
            else:
                print("Chat not found.")
        except Exception:
            print("Invalid command. Use /delete <chat_name>")
        return True
    
    def cmd_list_chats():
        """List all saved chats"""
        chats = chat_manager.list_chats()
        if chats:
            print(f"Active chat: {current_chat}")
            for chat_name in chats:
                print(chat_name)
        else:
            print("No chats found.")
        return True
    
    def cmd_help():
        """Show this help message with all available commands"""
        print("Available commands:")
        print("==================")
        for cmd_name, cmd_info in cmd_registry.get_all_commands().items():
            print(f"{cmd_name:<20} - {cmd_info['description']}")
        return True
    
    def cmd_exit():
        """Exit the chat application"""
        return False
    
    # Register all commands
    cmd_registry.register("/list models", "List and select available AI models", cmd_list_models)
    cmd_registry.register("/set stream", "Enable or disable streaming responses (true/false)", cmd_set_stream)
    cmd_registry.register("/set system", "Set the system prompt for the AI", cmd_set_system)
    cmd_registry.register("/new", "Start a new chat session", cmd_new)
    cmd_registry.register("/save", "Save the current chat with a given name", cmd_save)
    cmd_registry.register("/load", "Load a previously saved chat", cmd_load)
    cmd_registry.register("/delete", "Delete a saved chat", cmd_delete)
    cmd_registry.register("/list chats", "List all saved chats", cmd_list_chats)
    cmd_registry.register("/help", "Show this help message with all available commands", cmd_help)
    cmd_registry.register("/exit", "Exit the chat application", cmd_exit)

    while True:
        user_input = input("> ")
        
        # Check if input is a command (starts with /)
        if user_input.startswith("/"):
            command_handled = False
            
            # Handle commands
            if user_input == "/list models":
                cmd_registry.execute_command("/list models")
                command_handled = True
            elif user_input.startswith("/set stream "):
                try:
                    value = user_input.split(" ")[2]
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
            elif user_input == "/new":
                cmd_registry.execute_command("/new")
                command_handled = True
            elif user_input.startswith("/save "):
                try:
                    chat_name = user_input.split(" ", 1)[1]
                    cmd_registry.execute_command("/save", chat_name)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /save <chat_name>")
                    command_handled = True
            elif user_input.startswith("/load "):
                try:
                    chat_name = user_input.split(" ", 1)[1]
                    cmd_registry.execute_command("/load", chat_name)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /load <chat_name>")
                    command_handled = True
            elif user_input.startswith("/delete "):
                try:
                    chat_name = user_input.split(" ", 1)[1]
                    cmd_registry.execute_command("/delete", chat_name)
                    command_handled = True
                except IndexError:
                    print("Invalid command. Use /delete <chat_name>")
                    command_handled = True
            elif user_input == "/list chats":
                cmd_registry.execute_command("/list chats")
                command_handled = True
            elif user_input == "/help":
                cmd_registry.execute_command("/help")
                command_handled = True
            elif user_input == "/exit":
                if not cmd_registry.execute_command("/exit"):
                    break
                command_handled = True
            
            # If command wasn't handled, show error
            if not command_handled:
                print(f"Command '{user_input}' does not exist. Type /help to see available commands.")
        else:
            # Regular message, send to AI
            chat.send_message(user_input, history)
            chat_manager.save_chat(current_chat, history)

if __name__ == "__main__":
    main()
