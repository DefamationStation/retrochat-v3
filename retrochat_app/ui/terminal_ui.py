"""
Handles terminal-based user interface for the chat application.
"""
import re # Added import re
# Adjusted import path for LLMClient
from retrochat_app.api.llm_client import LLMClient
from retrochat_app.core.session_manager import SessionManager # Added SessionManager import
# import shlex # For parsing command arguments # Removed, moved to command_processor
import colorama # Added colorama
from rich.console import Console
from rich.markdown import Markdown
# import pyperclip # For clipboard operations # Removed, moved to command_processor

# Import the new handlers
from .command_processor import process_command
from .display_handler import show_help, show_system_info, render_message


colorama.init(autoreset=True) # Initialize colorama with autoreset

class TerminalUI:
    """
    Manages the chat interface in the terminal.
    """
    def __init__(self, llm_client: LLMClient, session_manager: SessionManager): # Added session_manager
        self.llm_client = llm_client
        self.session_manager = session_manager # Initialize SessionManager
        self.show_thoughts = False # Default to hiding thoughts
        self.console = Console() # Initialize Rich Console

    # _print_help method removed (moved to display_handler.py)

    # _handle_command method removed (moved to command_processor.py)

    # _print_info method removed (moved to display_handler.py)

    # start_chat method removed as it seems to be an older version of run()

    # display_message method removed (moved to display_handler.py)

    def run(self):
        # show_help(self.console) # Show help at the start
        render_message(self.console, "system", "Welcome to RetroChat! Type /help for commands.")
        self.session_manager.load_session() # load_session() handles creating a new one if needed.

        while True:
            try:
                # current_session_id = self.session_manager.get_current_session_id() # Removed session ID display
                # if current_session_id: # Removed session ID display
                #     self.console.print(f"(Session: {current_session_id})", style="dim") # Removed session ID display
                
                input_prompt = "" # Use an empty prompt for the input line
                user_input = self.console.input(input_prompt)
            except KeyboardInterrupt:
                render_message(self.console, "system", "\\\\nExiting...")
                break
            except EOFError: # Added EOFError handling for consistency with original start_chat
                render_message(self.console, "system", "\\\\nExiting chat. Goodbye!")
                break


            if user_input.startswith("/"):
                if process_command(self, user_input): # Pass self (TerminalUI instance)
                    break # Exit command was given
                continue

            if not user_input.strip():
                continue

            self.session_manager.add_message_to_history("user", user_input)
            conversation_history = self.session_manager.get_conversation_history()
            
            api_messages = []
            if self.llm_client.system_prompt: # Add system prompt if it exists
                api_messages.append({"role": "system", "content": self.llm_client.system_prompt})
            
            # Prepare messages for LLMClient, excluding any non-essential fields for the API
            # and ensuring correct order if system prompt was added
            api_messages.extend([{k: v for k, v in msg.items() if k in ['role', 'content']} for msg in conversation_history])


            try:
                is_stream = self.llm_client.stream
                if is_stream:
                    full_response_content = ""
                    # interim_response_for_display = "" # Not directly used for display here
                    
                    # Use a buffer for streamed Markdown to avoid printing partial Markdown constructs
                    stream_buffer = ""
                    for chunk in self.llm_client.stream_chat_message(api_messages):
                        if isinstance(chunk, dict) and chunk.get('type') == 'thought':
                            if self.show_thoughts:
                                # Pass self.show_thoughts to render_message
                                render_message(self.console, "system", chunk['content'], is_thought=True, show_thoughts_flag=self.show_thoughts)
                        elif isinstance(chunk, str):
                            full_response_content += chunk
                            stream_buffer += chunk
                            # Render the accumulated buffer. This is a simple approach.
                            # For perfect Markdown streaming, one might need to parse Markdown structure.
                            # We print the new chunk directly, assuming it's text.
                            # For a better streaming display of Markdown, one might print char by char or use a more complex buffer.
                            self.console.print(chunk, style="yellow", end="") # Stream output directly

                    self.console.print() # Ensure a newline after streaming is complete
                    
                    if full_response_content:
                        self.session_manager.add_message_to_history("assistant", full_response_content)
                else:
                    response_content = self.llm_client.send_chat_message_full_history(api_messages)
                    response_text = response_content if response_content is not None else "Error: No response from LLM."
                    
                    # Handle thoughts if they were part of a non-streamed response (hypothetical)
                    # This part depends on how llm_client might return thoughts in non-streaming mode.
                    # For now, assuming thoughts are primarily handled via the streaming path or embedded in response_text.
                    # If response_text contains <think> tags, it will be processed by session_manager.

                    self.session_manager.add_message_to_history("assistant", response_text)
                    
                    processed_history = self.session_manager.get_conversation_history()
                    if processed_history and processed_history[-1]["role"] == "assistant":
                        display_text_with_ids = processed_history[-1]["content"] # This content has IDs
                        
                        # Strip thoughts for display if not self.show_thoughts
                        final_display_text = display_text_with_ids
                        if not self.show_thoughts:
                            final_display_text = re.sub(r"<think>.*?</think>", "", final_display_text, flags=re.DOTALL).strip()
                        else:
                            # If showing thoughts, style them (basic styling here, could be enhanced)
                            final_display_text = re.sub(r"<think>(.*?)</think>", 
                                                       lambda m: colorama.Fore.LIGHTBLACK_EX + "Thinking: " + m.group(1).strip() + colorama.Style.RESET_ALL + " ", 
                                                       final_display_text, flags=re.DOTALL).strip()

                        render_message(self.console, "assistant", final_display_text, show_thoughts_flag=self.show_thoughts)
                    else: 
                        render_message(self.console, "assistant", response_text, is_error=response_text.startswith("Error:"), show_thoughts_flag=self.show_thoughts)

            except Exception as e:
                render_message(self.console, "system", f"Error during LLM communication: {e}", is_error=True, show_thoughts_flag=self.show_thoughts)
