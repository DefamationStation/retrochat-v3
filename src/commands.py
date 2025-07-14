"""
Command handler for slash commands
"""
import sys
from typing import Dict, Callable, List, Optional, Any
from abc import ABC, abstractmethod

from .chat_manager import ChatManager
from .config import ConfigManager
from .providers.factory import list_available_providers


class Command(ABC):
    """Base class for commands"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Command description"""
        pass
    
    @property
    def aliases(self) -> List[str]:
        """Command aliases"""
        return []
    
    @abstractmethod
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        """Execute the command"""
        pass


class HelpCommand(Command):
    """Show help information"""
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "Show help information"
    
    @property
    def aliases(self) -> List[str]:
        return ["h", "?"]
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        from .commands import get_all_commands  # Avoid circular import
        
        if args and args[0]:
            # Show help for specific command
            commands = get_all_commands()
            command_name = args[0].lower()
            
            for cmd in commands:
                if cmd.name == command_name or command_name in cmd.aliases:
                    return f"Command: /{cmd.name}\nDescription: {cmd.description}"
            
            return f"Unknown command: {command_name}"
        
        # Show general help
        commands = get_all_commands()
        help_text = "Available commands:\n"
        
        for cmd in commands:
            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            help_text += f"  /{cmd.name}{aliases} - {cmd.description}\n"
        
        help_text += "\nUse '/help <command>' for detailed help on a specific command."
        return help_text


class ClearCommand(Command):
    """Clear the current conversation"""
    
    @property
    def name(self) -> str:
        return "clear"
    
    @property
    def description(self) -> str:
        return "Clear the current conversation"
    
    @property
    def aliases(self) -> List[str]:
        return ["c", "new"]
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        chat_manager.start_new_conversation()
        return "Started a new conversation."


class ModelsCommand(Command):
    """List available models"""
    
    @property
    def name(self) -> str:
        return "models"
    
    @property
    def description(self) -> str:
        return "List available models"
    
    @property
    def aliases(self) -> List[str]:
        return ["m"]
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        try:
            models = chat_manager.list_models()
            current_model = chat_manager.get_model()
            
            if not models:
                return "No models available."
            
            result = "Available models:\n"
            for model in models:
                marker = " (current)" if model == current_model else ""
                result += f"  {model}{marker}\n"
            
            return result.strip()
        except Exception as e:
            return f"Error listing models: {e}"


class ModelCommand(Command):
    """Set the current model"""
    
    @property
    def name(self) -> str:
        return "model"
    
    @property
    def description(self) -> str:
        return "Set the current model. Usage: /model <model_name>"
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        if not args:
            current_model = chat_manager.get_model()
            return f"Current model: {current_model or 'None'}"
        
        model_name = args[0]
        try:
            available_models = chat_manager.list_models()
            
            if model_name not in available_models:
                return f"Model '{model_name}' not found. Use '/models' to see available models."
            
            chat_manager.set_model(model_name)
            return f"Switched to model: {model_name}"
        except Exception as e:
            return f"Error setting model: {e}"


class StatusCommand(Command):
    """Show system status"""
    
    @property
    def name(self) -> str:
        return "status"
    
    @property
    def description(self) -> str:
        return "Show system status"
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        result = "System Status:\n"
        
        # Provider status
        result += f"Provider: {chat_manager.provider_name}\n"
        is_available = chat_manager.is_provider_available()
        result += f"Provider Available: {'Yes' if is_available else 'No'}\n"
        
        # Current model
        current_model = chat_manager.get_model()
        result += f"Current Model: {current_model or 'None'}\n"
        
        # Conversation info
        conversation = chat_manager.get_current_conversation()
        if conversation:
            result += f"Current Chat: {conversation.title}\n"
            result += f"Messages: {len(conversation.messages)}\n"
        else:
            result += "Current Chat: None\n"
        
        # Available providers
        providers = list_available_providers()
        result += f"Available Providers: {', '.join(p for p, available in providers.items() if available)}\n"
        
        return result


class ProvidersCommand(Command):
    """List available providers"""
    
    @property
    def name(self) -> str:
        return "providers"
    
    @property
    def description(self) -> str:
        return "List available providers"
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        providers = list_available_providers()
        
        if not providers:
            return "No providers available."
        
        result = "Available providers:\n"
        for name, available in providers.items():
            status = "✓" if available else "✗"
            current = " (current)" if name == chat_manager.provider_name else ""
            result += f"  {status} {name}{current}\n"
        
        return result.strip()


class ExitCommand(Command):
    """Exit the application"""
    
    @property
    def name(self) -> str:
        return "exit"
    
    @property
    def description(self) -> str:
        return "Exit the application"
    
    @property
    def aliases(self) -> List[str]:
        return ["quit", "q"]
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        print("Goodbye!")
        sys.exit(0)


class ConfigCommand(Command):
    """Show or modify configuration"""
    
    @property
    def name(self) -> str:
        return "config"
    
    @property
    def description(self) -> str:
        return "Show configuration. Usage: /config [key] [value]"
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        if not args:
            # Show current config
            config = config_manager.load_config()
            chat_config = config.chat or config_manager.get_chat_config()
            result = "Current Configuration:\n"
            result += f"Default Provider: {config.default_provider}\n"
            result += f"System Prompt: {chat_config.system_prompt}\n"
            result += f"Max Tokens: {chat_config.max_tokens}\n"
            result += f"Temperature: {chat_config.temperature}\n"
            result += f"Stream: {chat_config.stream}\n"
            return result
        
        if len(args) == 1:
            # Show specific config value
            key = args[0]
            config = config_manager.load_config()
            chat_config = config.chat or config_manager.get_chat_config()
            
            if key == "provider":
                return f"Default Provider: {config.default_provider}"
            elif key == "system_prompt":
                return f"System Prompt: {chat_config.system_prompt}"
            elif key == "max_tokens":
                return f"Max Tokens: {chat_config.max_tokens}"
            elif key == "temperature":
                return f"Temperature: {chat_config.temperature}"
            elif key == "stream":
                return f"Stream: {chat_config.stream}"
            else:
                return f"Unknown config key: {key}"
        
        # Set config value (simplified for demo)
        return "Configuration modification not implemented in this demo."


class ThinkingCommand(Command):
    """Toggle thinking display for reasoning models"""
    
    @property
    def name(self) -> str:
        return "thinking"
    
    @property
    def description(self) -> str:
        return "Toggle thinking display for reasoning models. Usage: /thinking [on|off]"
    
    @property
    def aliases(self) -> List[str]:
        return ["think"]
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        config = config_manager.load_config()
        chat_config = config.chat
        
        if not chat_config:
            return "No chat configuration found."
        
        if not args:
            status = "enabled" if chat_config.show_thinking else "disabled"
            return f"Thinking display is currently {status}."
        
        arg = args[0].lower()
        if arg in ('on', 'true', '1', 'yes', 'enable'):
            chat_config.show_thinking = True
            status = "enabled"
        elif arg in ('off', 'false', '0', 'no', 'disable'):
            chat_config.show_thinking = False
            status = "disabled"
        else:
            return f"Invalid argument: {arg}. Use 'on' or 'off'."
        
        try:
            config_manager.save_config()
            return f"Thinking display {status}."
        except Exception as e:
            return f"Error saving configuration: {e}"


class ParamsCommand(Command):
    """View and modify chat parameters"""
    
    @property
    def name(self) -> str:
        return "params"
    
    @property
    def description(self) -> str:
        return "View or modify chat parameters. Usage: /params [param=value] [param=value] ..."
    
    @property
    def aliases(self) -> List[str]:
        return ["parameters", "settings"]
    
    def execute(self, args: List[str], chat_manager: ChatManager, config_manager: ConfigManager) -> Optional[str]:
        if not args:
            # Show current parameters
            config = config_manager.load_config()
            chat_config = config.chat
            
            if not chat_config:
                return "No chat configuration found."
            
            result = "Current chat parameters:\n"
            result += f"  temperature: {chat_config.temperature}\n"
            result += f"  max_tokens: {chat_config.max_tokens}\n"
            result += f"  top_p: {chat_config.top_p}\n"
            result += f"  top_k: {chat_config.top_k}\n"
            result += f"  frequency_penalty: {chat_config.frequency_penalty}\n"
            result += f"  presence_penalty: {chat_config.presence_penalty}\n"
            result += f"  repeat_penalty: {chat_config.repeat_penalty}\n"
            result += f"  stream: {chat_config.stream}\n"
            result += f"  show_thinking: {chat_config.show_thinking}\n"
            if chat_config.seed is not None:
                result += f"  seed: {chat_config.seed}\n"
            if chat_config.stop_sequences:
                result += f"  stop_sequences: {chat_config.stop_sequences}\n"
            
            return result.strip()
        
        # Modify parameters
        config = config_manager.load_config()
        chat_config = config.chat
        
        if not chat_config:
            return "No chat configuration found."
        
        changes = []
        for arg in args:
            if '=' not in arg:
                return f"Invalid parameter format: {arg}. Use param=value"
            
            param, value = arg.split('=', 1)
            param = param.strip()
            value = value.strip()
            
            try:
                # Handle different parameter types
                if param == "temperature":
                    chat_config.temperature = float(value)
                elif param == "max_tokens":
                    chat_config.max_tokens = int(value)
                elif param == "top_p":
                    chat_config.top_p = float(value)
                elif param == "top_k":
                    chat_config.top_k = int(value)
                elif param == "frequency_penalty":
                    chat_config.frequency_penalty = float(value)
                elif param == "presence_penalty":
                    chat_config.presence_penalty = float(value)
                elif param == "repeat_penalty":
                    chat_config.repeat_penalty = float(value)
                elif param == "stream":
                    chat_config.stream = value.lower() in ('true', '1', 'yes', 'on')
                elif param == "show_thinking":
                    chat_config.show_thinking = value.lower() in ('true', '1', 'yes', 'on')
                elif param == "seed":
                    if value.lower() in ('none', 'null', ''):
                        chat_config.seed = None
                    else:
                        chat_config.seed = int(value)
                elif param == "stop_sequences":
                    if value.lower() in ('none', 'null', ''):
                        chat_config.stop_sequences = None
                    else:
                        # Parse comma-separated list
                        chat_config.stop_sequences = [s.strip() for s in value.split(',') if s.strip()]
                else:
                    return f"Unknown parameter: {param}"
                
                changes.append(f"{param}={value}")
                
            except ValueError as e:
                return f"Invalid value for {param}: {value} ({e})"
        
        # Save configuration
        try:
            config_manager.save_config()
            return f"Updated parameters: {', '.join(changes)}"
        except Exception as e:
            return f"Error saving configuration: {e}"


# Registry of all commands
def get_all_commands() -> List[Command]:
    """Get all available commands"""
    return [
        HelpCommand(),
        ClearCommand(),
        ModelsCommand(),
        ModelCommand(),
        StatusCommand(),
        ProvidersCommand(),
        ExitCommand(),
        ConfigCommand(),
        ParamsCommand(),
        ThinkingCommand(),
    ]


class CommandHandler:
    """Handles slash commands"""
    
    def __init__(self, chat_manager: ChatManager, config_manager: ConfigManager):
        self.chat_manager = chat_manager
        self.config_manager = config_manager
        self.commands: Dict[str, Command] = {}
        
        # Register commands
        for cmd in get_all_commands():
            self.commands[cmd.name] = cmd
            for alias in cmd.aliases:
                self.commands[alias] = cmd
    
    def is_command(self, text: str) -> bool:
        """Check if text is a command"""
        return text.startswith('/')
    
    def parse_command(self, text: str) -> tuple[str, List[str]]:
        """Parse command and arguments"""
        if not text.startswith('/'):
            return "", []
        
        parts = text[1:].strip().split()
        if not parts:
            return "", []
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        return command, args
    
    def execute_command(self, text: str) -> Optional[str]:
        """Execute a command"""
        command_name, args = self.parse_command(text)
        
        if not command_name:
            return "Invalid command format. Use '/help' for available commands."
        
        if command_name not in self.commands:
            return f"Unknown command: {command_name}. Use '/help' for available commands."
        
        command = self.commands[command_name]
        try:
            return command.execute(args, self.chat_manager, self.config_manager)
        except Exception as e:
            return f"Error executing command: {e}"
