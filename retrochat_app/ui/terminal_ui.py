"""
Handles terminal-based user interface for the chat application.
"""
import re
import colorama
from rich.console import Console
from rich.markdown import Markdown # Keep for simple user messages or system messages
from rich.text import Text
from rich.panel import Panel

from retrochat_app.api.llm_client import LLMClient
from retrochat_app.core.session_manager import SessionManager

# Import the new handlers and formatter
from .command_processor import process_command
from .display_handler import render_message, log_error # Keep for user messages and simple system messages
from .code_block_formatter import CodeBlockFormatter

# Import logger setup
from retrochat_app.utils import logger_setup # Added
import logging # Added

colorama.init(autoreset=True) # Initialize colorama with autoreset

class TerminalUI:
    """
    Manages the chat interface in the terminal.
    """
    def __init__(self, llm_client: LLMClient, session_manager: SessionManager):
        self.logger = logging.getLogger(__name__) # Added
        self.llm_client = llm_client
        self.session_manager = session_manager
        self.show_thoughts = False
        self.console = Console()
        # Pass the session_manager.current_session_data directly
        self.code_block_formatter = CodeBlockFormatter(self.session_manager.current_session_data)
        self.logger.debug("TerminalUI initialized.") # Added

    def _display_loaded_history(self):
        """Displays the conversation history from the currently loaded session."""
        self.logger.debug("Attempting to display loaded history.") # Added
        history = self.session_manager.get_conversation_history()
        if history:
            self.console.print(Panel("[cyan]Resuming previous session...[/cyan]", expand=False))
            self.logger.debug(f"Found {len(history)} messages in history.") # Added
            for i, message in enumerate(history):
                role = message.get("role")
                content = message.get("content")
                self.logger.debug(f"Processing message {i+1}/{len(history)} - Role: {role}, Content (first 50): {content[:50] if content else 'None'}") # Added
                if role and content:
                    # Mimic existing display logic for user and assistant messages
                    if role == "user":
                        # User messages are typically simpler, directly rendered.
                        render_message(self.console, "user", content)
                    elif role == "assistant":
                        # Assistant messages might contain code blocks and need formatting.
                        display_content = content # Start with original content
                        if not self.show_thoughts:
                            # Remove .strip() from the end of this line
                            display_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
                        else:
                            # Remove .strip() from the end of this line
                            display_content = re.sub(r"<think>(.*?)</think>",
                                                     lambda m: colorama.Fore.LIGHTBLACK_EX + "Thinking: " + m.group(1).strip() + colorama.Style.RESET_ALL + " ",
                                                     content, flags=re.DOTALL)
                        
                        self.logger.debug(f"Assistant message content for formatter (first 100): {display_content[:100]}") # Added
                        if display_content: # Ensure there's content to display
                            renderables = self.code_block_formatter.format_for_display(display_content)
                            self.logger.debug(f"Formatter returned {len(renderables)} renderables for assistant message.") # Added
                            for renderable in renderables:
                                if isinstance(renderable, Panel):  # Code blocks
                                    self.console.print(renderable)
                                elif isinstance(renderable, Text) and renderable.plain.startswith("CodeID"):
                                    self.console.print(renderable)  # CodeID labels
                                elif isinstance(renderable, Text) and renderable.plain == "\\n":
                                    self.console.print(renderable) # Newlines for spacing
                                else:
                                    # Apply yellow style to other content (Markdown, other Text)
                                    self.console.print(renderable, style="yellow")
            self.console.print(Panel("[cyan]End of previous session.[/cyan]", expand=False))


    def run(self):
        self.logger.info("TerminalUI run method started.") # Added
        render_message(self.console, "system", "Welcome to RetroChat! Type /help for commands.")
        if self.session_manager.load_session(): # Returns True if a session was loaded
            self.logger.info("Session loaded successfully.") # Added
            # CodeBlockFormatter is already initialized with current_session_data,
            # so no explicit load_from_session call is needed here.
            # We might need to re-initialize or update the formatter if session_data reference changes
            # or if load_session creates a new session_data object internally.
            # For now, assuming session_manager.current_session_data is the single source of truth.
            self.code_block_formatter = CodeBlockFormatter(self.session_manager.current_session_data) # Re-initialize with potentially new session data
            self._display_loaded_history() 
        else:
            self.logger.info("No existing session loaded or new session started.") # Added
            # If no session was loaded (e.g., first run or new session created by load_session implicitly)
            # ensure the formatter is using the (potentially new) session_data object.
            self.code_block_formatter = CodeBlockFormatter(self.session_manager.current_session_data)
            self.code_block_formatter.reset() # Ensure a clean state for a new session

        while True:
            try:
                input_prompt = ""
                user_input = self.console.input(input_prompt)
            except KeyboardInterrupt:
                render_message(self.console, "system", "\\\\nExiting...")
                break
            except EOFError:
                render_message(self.console, "system", "\\\\nExiting chat. Goodbye!")
                break

            if user_input.startswith("/"):
                if process_command(self, user_input): 
                    break 
                continue

            if not user_input.strip():
                continue

            self.session_manager.add_message_to_history("user", user_input)
            
            conversation_history = self.session_manager.get_conversation_history()
            
            api_messages = []
            if self.llm_client.system_prompt:
                api_messages.append({"role": "system", "content": self.llm_client.system_prompt})
            
            # Corrected list comprehension
            api_messages.extend([{k: v for k, v in msg.items() if k in ['role', 'content']} for msg in conversation_history])

            try:
                is_stream = self.llm_client.stream
                assistant_response_content = ""

                if is_stream:
                    stream_buffer = ""
                    with self.console.status("[yellow]Assistant is thinking...[/yellow]", spinner="dots") as status:
                        for chunk in self.llm_client.stream_chat_message(api_messages):
                            status.stop() # Stop spinner once first chunk arrives
                            if isinstance(chunk, dict) and chunk.get('type') == 'thought':
                                if self.show_thoughts:
                                    render_message(self.console, "system", chunk['content'], is_thought=True, show_thoughts_flag=self.show_thoughts)
                            elif isinstance(chunk, str):
                                assistant_response_content += chunk
                                self.console.print(chunk, end="") 
                        self.console.print()
                else: # Non-streaming
                    with self.console.status("[yellow]Assistant is thinking...[/yellow]", spinner="dots") as status:
                        raw_llm_response = self.llm_client.send_chat_message_full_history(api_messages)
                    assistant_response_content = raw_llm_response if raw_llm_response is not None else "Error: No response from LLM."

                self.session_manager.add_message_to_history("assistant", assistant_response_content)

                display_content = assistant_response_content
                if not assistant_response_content.startswith("Error:"):
                    if self.show_thoughts:
                        display_content = re.sub(r"<think>(.*?)</think>",
                                                 lambda m: colorama.Fore.LIGHTBLACK_EX + "Thinking: " + m.group(1).strip() + colorama.Style.RESET_ALL + " ",
                                                 assistant_response_content, flags=re.DOTALL).strip()
                    else:
                        display_content = re.sub(r"<think>.*?</think>", "", assistant_response_content, flags=re.DOTALL).strip()
                
                if display_content:
                    renderables = self.code_block_formatter.format_for_display(display_content)
                    for renderable in renderables:
                        if isinstance(renderable, Panel):  # Code blocks
                            self.console.print(renderable)
                        elif isinstance(renderable, Text) and renderable.plain.startswith("CodeID"):
                            self.console.print(renderable)  # CodeID labels
                        elif isinstance(renderable, Text) and renderable.plain == "\n":
                            self.console.print(renderable) # Newlines for spacing
                        else:
                            # Apply yellow style to other content (Markdown, other Text)
                            self.console.print(renderable, style="yellow")

                    if not renderables and not is_stream: 
                        self.console.print(style="yellow") # Print with yellow style if nothing else rendered

            except Exception as e:
                log_error(self.console, f"Error during LLM communication: {e}")
