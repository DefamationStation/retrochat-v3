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


colorama.init(autoreset=True) # Initialize colorama with autoreset

class TerminalUI:
    """
    Manages the chat interface in the terminal.
    """
    def __init__(self, llm_client: LLMClient, session_manager: SessionManager):
        self.llm_client = llm_client
        self.session_manager = session_manager
        self.show_thoughts = False
        self.console = Console()
        self.code_block_formatter = CodeBlockFormatter() # Initialize CodeBlockFormatter

    def run(self):
        render_message(self.console, "system", "Welcome to RetroChat! Type /help for commands.")
        self.session_manager.load_session()
        self.code_block_formatter.reset() # Reset formatter for the initial session

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
                    # if not is_stream: 
                    #      self.console.print("Assistant: ", end="")
                    
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
