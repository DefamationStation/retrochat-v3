"""
CLI interface for the chat application
"""
import sys
import os
from typing import Optional

# Try to import colorama, fallback to no colors if not available
try:
    import colorama
    colorama.init()  # Initialize colorama for Windows
    HAS_COLORAMA = True
    FORE_RED = colorama.Fore.RED
    FORE_GREEN = colorama.Fore.GREEN
    FORE_YELLOW = colorama.Fore.YELLOW
    FORE_BLUE = colorama.Fore.BLUE
    FORE_MAGENTA = colorama.Fore.MAGENTA
    FORE_CYAN = colorama.Fore.CYAN
    FORE_WHITE = colorama.Fore.WHITE
    FORE_RESET = colorama.Fore.RESET
    STYLE_BRIGHT = colorama.Style.BRIGHT
    STYLE_RESET = colorama.Style.RESET_ALL
except ImportError:
    HAS_COLORAMA = False
    # Fallback - no colors
    FORE_RED = ""
    FORE_GREEN = ""
    FORE_YELLOW = ""
    FORE_BLUE = ""
    FORE_MAGENTA = ""
    FORE_CYAN = ""
    FORE_WHITE = ""
    FORE_RESET = ""
    STYLE_BRIGHT = ""
    STYLE_RESET = ""

from .config import ConfigManager
from .chat_manager import ChatManager
from .commands import CommandHandler


def colored_print(text: str, color: str = "", style: str = "", end: str = "\n") -> None:
    """Print colored text if colorama is available"""
    if HAS_COLORAMA and (color or style):
        print(f"{style}{color}{text}{STYLE_RESET}", end=end)
    else:
        print(text, end=end)


class CLI:
    """Command Line Interface for the chat application"""
    
    def __init__(self):
        from .config import ConfigManager
        from .chat_manager import ChatManager
        from .commands import CommandHandler
        
        self.config_manager = ConfigManager()
        
        # Load configuration
        try:
            config = self.config_manager.load_config()
            provider_config = self.config_manager.get_provider_config()
            chat_config = self.config_manager.get_chat_config()
        except Exception as e:
            colored_print(f"Error loading configuration: {e}", FORE_RED)
            sys.exit(1)
        
        # Initialize chat manager
        try:
            self.chat_manager = ChatManager(
                provider_name=config.default_provider,
                provider_config=provider_config.__dict__,
                chat_config=chat_config.__dict__
            )
        except Exception as e:
            colored_print(f"Error initializing chat manager: {e}", FORE_RED)
            sys.exit(1)
        
        # Initialize command handler
        self.command_handler = CommandHandler(self.chat_manager, self.config_manager)
        
        # Check provider availability
        if not self.chat_manager.is_provider_available():
            colored_print(f"Warning: Provider '{config.default_provider}' is not available.", FORE_YELLOW)
    
    def print_welcome(self):
        """Print welcome message"""
        colored_print("=" * 60, FORE_CYAN)
        colored_print("   RetroChat CLI v1.0.0", FORE_CYAN, STYLE_BRIGHT)
        colored_print("   A minimalistic chat application with LM Studio", FORE_CYAN)
        colored_print("=" * 60, FORE_CYAN)
        colored_print("")
        colored_print("Type '/help' for available commands or just start chatting!", FORE_GREEN)
        colored_print("Use Ctrl+C to exit at any time.", FORE_YELLOW)
        colored_print("")
    
    def print_prompt(self):
        """Print input prompt"""
        if HAS_COLORAMA:
            print(f"{FORE_BLUE}You: {STYLE_RESET}", end="")
        else:
            print("You: ", end="")
    
    def print_assistant_response(self, content: str, streaming: bool = False):
        """Print assistant response"""
        if not streaming:
            colored_print(f"Assistant: {content}", FORE_GREEN)
        else:
            # For streaming, content comes in chunks
            if HAS_COLORAMA:
                print(f"{FORE_GREEN}Assistant: {STYLE_RESET}", end="", flush=True)
            else:
                print(content, end="", flush=True)
    
    def handle_streaming_response(self, user_input: str) -> None:
        """Handle streaming response with proper reasoning model support"""
        colored_print("Assistant: ", FORE_GREEN, end="")
        
        full_response = ""
        show_thinking = self.config_manager.get_chat_config().show_thinking
        
        try:
            # Collect all chunks first to handle thinking tags properly
            chunks = []
            for chunk in self.chat_manager.send_message_stream(user_input):
                chunks.append(chunk)
                full_response += chunk
            
            # Now process and display with proper thinking handling
            if show_thinking:
                # Display everything if show_thinking is enabled
                for chunk in chunks:
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
            else:
                # Filter out thinking content
                if "<think>" in full_response and "</think>" in full_response:
                    # Remove thinking content
                    import re
                    clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL)
                    sys.stdout.write(clean_response)
                    sys.stdout.flush()
                else:
                    # No thinking tags, display normally
                    for chunk in chunks:
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
            
            print()  # New line after streaming
            
        except Exception as e:
            print(f"\nStreaming error: {e}", flush=True)
            colored_print("Make sure LM Studio is running and has a model loaded.", FORE_YELLOW)
    
    def handle_user_input(self, user_input: str) -> bool:
        """Handle user input. Returns False if should exit."""
        user_input = user_input.strip()
        
        if not user_input:
            return True
        
        # Check if it's a command
        if self.command_handler.is_command(user_input):
            try:
                result = self.command_handler.execute_command(user_input)
                if result:
                    colored_print(result, FORE_CYAN)
            except KeyboardInterrupt:
                return False
            except Exception as e:
                colored_print(f"Command error: {e}", FORE_RED)
            return True
        
        # Regular chat message
        try:
            # Check if streaming is enabled
            config = self.config_manager.get_chat_config()
            if config.stream:
                self.handle_streaming_response(user_input)
            else:
                response = self.chat_manager.send_message(user_input, stream=False)
                # Handle <think> tags in non-streaming mode too
                content = response.content
                if "<think>" in content and "</think>" in content:
                    # Extract thinking and final content
                    parts = content.split("<think>", 1)
                    before_think = parts[0] if parts[0] else ""
                    
                    think_parts = parts[1].split("</think>", 1) if len(parts) > 1 else ["", ""]
                    thinking_content = think_parts[0] if think_parts[0] else ""
                    after_think = think_parts[1] if len(think_parts) > 1 else ""
                    
                    # Display the response
                    if config.show_thinking and thinking_content:
                        colored_print(f"Assistant: {before_think}", FORE_GREEN)
                        colored_print(f"[Thinking: {thinking_content}]", FORE_YELLOW)
                        colored_print(after_think, FORE_GREEN)
                    else:
                        colored_print(f"Assistant: {before_think}{after_think}", FORE_GREEN)
                else:
                    colored_print(f"Assistant: {content}", FORE_GREEN)
                
        except KeyboardInterrupt:
            colored_print("\nMessage cancelled.", FORE_YELLOW)
        except Exception as e:
            colored_print(f"Error: {e}", FORE_RED)
            colored_print("Make sure LM Studio is running and has a model loaded.", FORE_YELLOW)
        
        return True
    
    def run(self):
        """Run the CLI application"""
        self.print_welcome()
        
        # Start initial conversation
        try:
            self.chat_manager.start_new_conversation()
        except Exception as e:
            colored_print(f"Error starting conversation: {e}", FORE_RED)
            return
        
        # Main input loop
        try:
            while True:
                try:
                    self.print_prompt()
                    user_input = input()
                    
                    if not self.handle_user_input(user_input):
                        break
                        
                except EOFError:
                    # Handle Ctrl+D
                    colored_print("\nGoodbye!", FORE_CYAN)
                    break
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    colored_print("\nGoodbye!", FORE_CYAN)
                    break
                    
        except Exception as e:
            colored_print(f"Unexpected error: {e}", FORE_RED)
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        colored_print("\nGoodbye!", FORE_CYAN)
    except Exception as e:
        colored_print(f"Fatal error: {e}", FORE_RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
