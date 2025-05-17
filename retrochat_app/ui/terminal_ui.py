"""
Handles terminal-based user interface for the chat application.
"""
import re # Added import re
# Adjusted import path for LLMClient
from retrochat_app.api.llm_client import LLMClient
from retrochat_app.core.session_manager import SessionManager # Added SessionManager import
import shlex # For parsing command arguments
import colorama # Added colorama
from rich.console import Console
from rich.markdown import Markdown
import pyperclip # For clipboard operations

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

    def _print_help(self):
        # Using self.console.print for consistency
        self.console.print("Available commands:")
        self.console.print("  /help                          - Show this help message.")
        self.console.print("  /info                          - Show connection info, system prompt, and non-default parameters.")
        self.console.print("  /set <param> <value>           - Set a model parameter (e.g., /set temperature 0.5).")
        self.console.print("                                   Available params: model, temperature, max_tokens, top_p, presence_penalty, frequency_penalty, stream.")
        self.console.print('  /system <prompt>               - Set the system prompt (e.g., /system "You are a helpful assistant.").') # Corrected escaping
        self.console.print("  /system clear                  - Clear the system prompt.")
        self.console.print("  /params                        - Show current model parameters and system prompt.")
        self.console.print("  /history                       - Show the current conversation history for the active session.")
        self.console.print("  /chat reset                    - Clear the current conversation history for the active session.")
        self.console.print("  /chat new [id]                 - Start a new chat session (optional id).")
        self.console.print("  /chat load <session_id>        - Load a specific chat session.")
        self.console.print("  /chat list                     - List all available chat sessions.")
        self.console.print("  /chat delete <session_id>      - Delete a specific chat session.")
        self.console.print("  /chat rename <new_name>        - Rename the current active chat session.")
        self.console.print("  /chat current                  - Show the current session ID and metadata.")
        self.console.print("  /think show                    - Show AI thought process (styled, no tags).")
        self.console.print("  /think hide                    - Hide AI thought process.")
        self.console.print("  /copy <CodeID>                 - Copy the content of a specific code block to clipboard.")
        self.console.print("  /exit or /quit                 - Exit the chat.")
        self.console.print("-" * 30)

    def _handle_command(self, command_input: str):
        try:
            parts = shlex.split(command_input)
        except ValueError as e:
            self.console.print(f"[red]Error parsing command: {e}. Ensure quotes are properly matched.[/red]")
            return False

        if not parts:
            return False

        command = parts[0].lower()
        args = parts[1:]

        if command == "/info":
            self._print_info()
        elif command == "/set":
            if len(args) == 2:
                param_name, value = args[0], args[1]
                if param_name.lower() == "stream":
                    if value.lower() == "true": self.llm_client.set_parameter(param_name, True)
                    elif value.lower() == "false": self.llm_client.set_parameter(param_name, False)
                    else: self.console.print("[red]Invalid value for stream. Use 'true' or 'false'.[/red]")
                else:
                    self.llm_client.set_parameter(param_name, value)
            else:
                self.console.print("Usage: /set <param_name> <value>")
        elif command == "/system":
            if not args: self.console.print("Usage: /system <prompt_string> or /system clear")
            elif args[0].lower() == "clear": self.llm_client.set_system_prompt(None)
            else: self.llm_client.set_system_prompt(" ".join(args))
        elif command == "/params":
            params = self.llm_client.get_all_parameters()
            self.console.print("Current Parameters:") 
            for key, value in params.items():
                if key == "system_prompt" and value is None: self.console.print(f"  {key}: Not set")
                elif key == "system_prompt": self.console.print(f'  {key}: "{value}"')
                else: self.console.print(f"  {key}: {value}")
            self.console.print("-" * 30)
        elif command == "/history":
            history = self.session_manager.get_conversation_history()
            if not history: self.console.print("Conversation history is empty for the current session.")
            else:
                self.console.print("\\\\nConversation History:")
                for msg in history:
                    self.console.print(f"  {msg['role'].capitalize()}: {msg['content']}")
                self.console.print("-" * 30)
        elif command == "/chat": 
            if not args:
                self.console.print("Usage: /chat <reset|new|load|list|delete|current|rename>")
                return False
            
            sub_command = args[0].lower()
            if sub_command == "reset":
                self.session_manager.clear_current_session_history()
            elif sub_command == "new":
                new_session_id = args[1] if len(args) > 1 else None
                self.session_manager.new_session(new_session_id)
            elif sub_command == "load":
                if len(args) > 1:
                    self.session_manager.load_session(args[1])
                else:
                    self.console.print("Usage: /chat load <session_id>")
            elif sub_command == "list":
                sessions = self.session_manager.list_sessions()
                if not sessions:
                    self.console.print("No sessions found.")
                else:
                    self.console.print("Available Sessions:")
                    for s in sessions:
                        self.console.print(f"  ID: {s['id']}, Created: {s.get('created_at', 'N/A')}, Modified: {s.get('last_modified', 'N/A')}, Messages: {s.get('message_count', 0)}")
                    self.console.print("-" * 30)
            elif sub_command == "delete":
                if len(args) > 1:
                    self.session_manager.delete_session(args[1])
                else:
                    self.console.print("Usage: /chat delete <session_id>")
            elif sub_command == "current":
                session_id = self.session_manager.get_current_session_id()
                if session_id:
                    metadata = self.session_manager.get_current_session_metadata()
                    self.console.print(f"\\\\nCurrent Session ID: {session_id}")
                    self.console.print("  Metadata:")
                    for key, value in metadata.items():
                        self.console.print(f"    {key}: {value}")
                    self.console.print("-" * 30)
                else:
                    self.console.print("No active session.")
            elif sub_command == "rename": 
                if len(args) > 1:
                    new_name = args[1]
                    current_id = self.session_manager.get_current_session_id()
                    if not current_id:
                        self.console.print("[red]Error: No active session to rename.[/red]")
                    elif not new_name.strip():
                        self.console.print("[red]Error: New session name cannot be empty.[/red]")
                    else:
                        if self.session_manager.rename_session(current_id, new_name.strip()):
                            self.console.print(f"Session '{current_id}' renamed to '{new_name.strip()}'.")
                else:
                    self.console.print("Usage: /chat rename <new_name>")
            else:
                self.console.print(f"[red]Unknown chat command: /chat {sub_command}. Type /help for available commands.[/red]")
                
        elif command == "/think":
            if not args:
                self.console.print("Usage: /think <show|hide>")
            elif args[0].lower() == "show":
                self.show_thoughts = True
                self.console.print("AI thought process will now be shown.")
            elif args[0].lower() == "hide":
                self.show_thoughts = False
                self.console.print("AI thought process will now be hidden.")
            else:
                self.console.print("Usage: /think <show|hide>")
        elif command == "/copy":
            if len(args) == 1:
                block_id_str = args[0]
                code_content = self.session_manager.get_code_block(block_id_str)
                if code_content is not None:
                    try:
                        pyperclip.copy(code_content)
                        self.console.print(f"Code block [cyan]CodeID {block_id_str}[/cyan] copied to clipboard.")
                    except pyperclip.PyperclipException as e:
                        self.console.print(f"[red]Error copying to clipboard: {e}. Make sure you have a copy/paste mechanism installed (e.g., xclip or xsel on Linux, or that your environment supports clipboard operations).[/red]")
                else:
                    self.console.print(f"[red]Code block with ID '{block_id_str}' not found in the current session.[/red]")
            else:
                self.console.print("Usage: /copy <id>")
        elif command == "/exit" or command == "/quit":
            return True # Signal to exit
        else:
            self.console.print(f"[red]Unknown command: {command}. Type /help for available commands.[/red]")
        return False

    def _print_info(self):
        self.console.print("\\n--- Connection & Model Information ---")
        self.console.print(f"  Endpoint: {self.llm_client.endpoint}")
        self.console.print(f"  Model: {self.llm_client.model}")
        
        current_params = self.llm_client.get_all_parameters()
        default_params = self.llm_client.default_params

        self.console.print("\\n--- System Prompt ---")
        if current_params["system_prompt"]:
            self.console.print(f'  "{current_params["system_prompt"]}"')
        else:
            self.console.print("  Not set.")

        self.console.print("\\n--- Custom Parameters (Non-Default) ---")
        has_custom_params = False
        for key, current_value in current_params.items():
            if key == "system_prompt": continue
            # Ensure default_params[key] exists before comparing
            if key in default_params and current_value != default_params[key]:
                self.console.print(f"  {key}: {current_value} (Default: {default_params[key]})")
                has_custom_params = True
            # This condition handles parameters that might be in current_params but not in default_params
            # (e.g. if default_params is not exhaustive or params were added dynamically)
            elif key not in default_params and current_value is not None: 
                self.console.print(f"  {key}: {current_value}")
                has_custom_params = True
        
        if not has_custom_params:
            self.console.print("  All parameters are at their default values.")
        self.console.print("-" * 30)

    def start_chat(self):
        """
        Starts the interactive chat loop.
        """
        if not self.session_manager.load_session(): 
            pass 

        while True:
            try:
                user_input = input().strip() 
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    # Corrected string literal for /session
                    if user_input.lower().startswith("/chat") or user_input.lower().startswith("/session"): 
                        pass # Removed _reset_code_block_tracking call

                    if self._handle_command(user_input):
                        break 
                    continue

                self.session_manager.add_message_to_history("user", user_input)

                chat_history = self.session_manager.get_conversation_history()
                messages_for_api = []
                if self.llm_client.system_prompt:
                    messages_for_api.append({"role": "system", "content": self.llm_client.system_prompt})
                messages_for_api.extend(chat_history)

                raw_llm_response = None
                accumulated_streamed_content = []
                
                if self.llm_client.stream:
                    response_stream = self.llm_client.stream_chat_message(messages_for_api)
                    if response_stream:
                        try:
                            for chunk in response_stream:
                                accumulated_streamed_content.append(chunk)
                        except Exception as e: 
                            self.console.print(Markdown(f"[red]\\nError during streaming: {e}[/red]"))
                            accumulated_streamed_content.append(f"Error: Stream interrupted: {e}") 
                    raw_llm_response = "".join(accumulated_streamed_content)
                    
                    if not raw_llm_response and response_stream is None:
                         raw_llm_response = "Error: Failed to initiate stream with LLM."

                else: 
                    raw_llm_response = self.llm_client.send_chat_message_full_history(messages_for_api)
                    if raw_llm_response is None: 
                        raw_llm_response = "Error: No response from LLM."
                
                final_response_to_save_in_history = raw_llm_response 
                final_response_to_display_markdown = "" # Renamed for clarity

                if raw_llm_response and not raw_llm_response.startswith("Error:"):
                    interim_response_for_display = ""
                    if self.show_thoughts:
                        interim_response_for_display = re.sub(r"<think>(.*?)</think>", 
                                                           lambda m: colorama.Fore.LIGHTBLACK_EX + "Thinking: " + m.group(1).strip() + colorama.Style.RESET_ALL + " ", 
                                                           raw_llm_response, flags=re.DOTALL).strip()
                    else:
                        interim_response_for_display = re.sub(r"<think>.*?</think>", "", raw_llm_response, flags=re.DOTALL).strip()
                    
                    # Process for code block tagging
                    final_response_to_display_markdown = interim_response_for_display # Direct assignment, processing moved to SessionManager
                    
                    if final_response_to_save_in_history: 
                        self.session_manager.add_message_to_history("assistant", final_response_to_save_in_history) 
                        
                    if final_response_to_display_markdown:
                        self.console.print(Markdown(final_response_to_display_markdown), style="yellow")
                    
                elif raw_llm_response: 
                    self.console.print(Markdown(f"[red]{raw_llm_response}[/red]"))
                
            except KeyboardInterrupt:
                self.console.print("\\nExiting chat. Goodbye!")
                break
            except EOFError: 
                self.console.print("\\nExiting chat. Goodbye!")
                break
            except Exception as e:
                self.console.print(f"[red]An unexpected error occurred in the main loop: {e}[/red]")

    def display_message(self, role: str, text: str, is_error: bool = False, is_thought: bool = False):
        """
        Displays a message in the terminal, applying styles based on the role.
        Code blocks in assistant messages are processed by SessionManager before this.
        """
        if is_error:
            self.console.print(f"[red]{text}[/red]")
        elif is_thought:
            if self.show_thoughts:
                # Display thoughts with a specific style, perhaps less prominent
                self.console.print(f"[dim italic]Thought: {text}[/dim italic]")
        elif role == "user":
            self.console.print(Markdown(text), style="green") # User messages in green
        elif role == "assistant":
            # Assistant messages are already processed by SessionManager to include IDs
            # The text here should already have the [ID: X] tags embedded.
            self.console.print(Markdown(text), style="yellow") # Assistant messages in yellow
        else: # System messages or other roles
            self.console.print(text)

    def run(self):
        self.console.print("Welcome to RetroChat! Type /help for commands.")
        # self.session_manager.load_or_create_default_session() # Ensure a session is active
        self.session_manager.load_session() # load_session() handles creating a new one if needed.

        while True:
            try:
                current_session_id = self.session_manager.get_current_session_id()
                prompt_prefix = f"(Session: {current_session_id}) You: " if current_session_id else "You: "
                user_input = self.console.input(prompt_prefix)
            except KeyboardInterrupt:
                self.console.print("\\nExiting...")
                break

            if user_input.startswith("/"):
                if self._handle_command(user_input):
                    break # Exit command was given
                continue

            if not user_input.strip():
                continue

            self.session_manager.add_message_to_history("user", user_input)
            conversation_history = self.session_manager.get_conversation_history()
            
            # Prepare messages for LLMClient, excluding any non-essential fields for the API
            api_messages = [{k: v for k, v in msg.items() if k in ['role', 'content']} for msg in conversation_history]

            try:
                # is_stream = self.llm_client.get_parameter("stream")
                is_stream = self.llm_client.stream
                if is_stream:
                    full_response_content = ""
                    interim_response_for_display = ""
                    # for chunk in self.llm_client.send_request_stream(api_messages):
                    for chunk in self.llm_client.stream_chat_message(api_messages):
                        # chunk can be a string (content) or a dict (thought)
                        if isinstance(chunk, dict) and chunk.get('type') == 'thought':
                            if self.show_thoughts:
                                self.display_message("system", chunk['content'], is_thought=True)
                        elif isinstance(chunk, str):
                            full_response_content += chunk
                            interim_response_for_display += chunk
                            # Displaying chunk by chunk for streaming effect
                            # The Markdown object is recreated for each chunk, which might not be ideal for complex structures
                            # but works for simple text streaming.
                            # For a more robust streaming of Markdown, one might need a more sophisticated approach.
                            self.console.print(Markdown(chunk), style="yellow", end="") # Stream output
                    self.console.print() # Ensure a newline after streaming is complete
                    
                    if full_response_content:
                        # The full_response_content is processed by session_manager to handle code blocks
                        # and embed IDs. This happens *before* it's added to history.
                        self.session_manager.add_message_to_history("assistant", full_response_content)
                else:
                    # response_data = self.llm_client.send_request(api_messages)
                    response_content = self.llm_client.send_chat_message_full_history(api_messages)
                    
                    # Assuming send_chat_message_full_history now directly returns content or None
                    # And thoughts might be handled differently or not returned by this specific method.
                    # For simplicity, we'll assume it returns the text content directly.
                    # If it returns a dict like { "content": "...", "thought": "..." },
                    # the following lines would need adjustment.
                    # Based on llm_client.py, send_chat_message_full_history returns Optional[str] (the content)

                    response_text = response_content if response_content is not None else ""
                    # To handle thoughts, we'd need a different mechanism if not part of response_content
                    # For now, let's assume no separate "thought" field from non-streaming.
                    # if thought and self.show_thoughts:
                    #    self.display_message("system", thought, is_thought=True)
                    
                    # Add raw response to history, SessionManager will process it for code blocks
                    self.session_manager.add_message_to_history("assistant", response_text)
                    
                    # Retrieve the processed message from history for display
                    # This ensures that IDs are present if code blocks were found
                    processed_history = self.session_manager.get_conversation_history()
                    if processed_history and processed_history[-1]["role"] == "assistant":
                        display_text = processed_history[-1]["content"]
                        self.display_message("assistant", display_text)
                    else: # Fallback if something went wrong with history retrieval
                        self.display_message("assistant", response_text) 

            except Exception as e:
                self.display_message("system", f"Error: {e}", is_error=True)
