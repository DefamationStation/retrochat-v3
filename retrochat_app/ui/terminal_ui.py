"""
Handles terminal-based user interface for the chat application.
"""
import re # Added import re
# Adjusted import path for LLMClient
from retrochat_app.api.llm_client import LLMClient
from retrochat_app.core.session_manager import SessionManager # Added SessionManager import
import shlex # For parsing command arguments
import colorama # Added colorama

colorama.init(autoreset=True) # Initialize colorama with autoreset

class TerminalUI:
    """
    Manages the chat interface in the terminal.
    """
    def __init__(self, llm_client: LLMClient, session_manager: SessionManager): # Added session_manager
        self.llm_client = llm_client
        self.session_manager = session_manager # Initialize SessionManager
        self.show_thoughts = False # Default to hiding thoughts

    def _print_help(self):
        print("Available commands:")
        print("  /help                          - Show this help message.")
        print("  /info                          - Show connection info, system prompt, and non-default parameters.")
        print("  /set <param> <value>           - Set a model parameter (e.g., /set temperature 0.5).")
        print("                                   Available params: model, temperature, max_tokens, top_p, presence_penalty, frequency_penalty, stream.")
        print('  /system <prompt>               - Set the system prompt (e.g., /system "You are a helpful assistant.").')
        print("  /system clear                  - Clear the system prompt.")
        print("  /params                        - Show current model parameters and system prompt.")
        print("  /history                       - Show the current conversation history for the active session.")
        print("  /chat reset                    - Clear the current conversation history for the active session.")
        print("  /chat new [id]                 - Start a new chat session (optional id).")
        print("  /chat load <session_id>        - Load a specific chat session.")
        print("  /chat list                     - List all available chat sessions.")
        print("  /chat delete <session_id>      - Delete a specific chat session.")
        print("  /chat rename <new_name>        - Rename the current active chat session.") # New command
        print("  /chat current                  - Show the current session ID and metadata.")
        print("  /think show                    - Show AI thought process (styled, no tags).")
        print("  /think hide                    - Hide AI thought process.")
        print("  /exit or /quit                 - Exit the chat.")
        print("-" * 30)

    def _handle_command(self, command_input: str):
        try:
            parts = shlex.split(command_input)
        except ValueError as e:
            print(f"Error parsing command: {e}. Ensure quotes are properly matched.")
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
                    else: print("Invalid value for stream. Use 'true' or 'false'.")
                else:
                    self.llm_client.set_parameter(param_name, value)
            else:
                print("Usage: /set <param_name> <value>")
        elif command == "/system":
            if not args: print("Usage: /system <prompt_string> or /system clear")
            elif args[0].lower() == "clear": self.llm_client.set_system_prompt(None)
            else: self.llm_client.set_system_prompt(" ".join(args))
        elif command == "/params":
            params = self.llm_client.get_all_parameters()
            print("Current Parameters:") # Removed leading \\n
            for key, value in params.items():
                if key == "system_prompt" and value is None: print(f"  {key}: Not set")
                elif key == "system_prompt": print(f'  {key}: "{value}"')
                else: print(f"  {key}: {value}")
            print("-" * 30)
        elif command == "/history":
            history = self.session_manager.get_conversation_history()
            if not history: print("Conversation history is empty for the current session.")
            else:
                print("\\nConversation History:")
                for msg in history:
                    print(f"  {msg['role'].capitalize()}: {msg['content']}")
                print("-" * 30)
        elif command == "/chat": # Combined /chat and former /session commands
            if not args:
                print("Usage: /chat <reset|new|load|list|delete|current>")
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
                    # Message printed by session_manager or new_session if load fails
                else:
                    print("Usage: /chat load <session_id>")
            elif sub_command == "list":
                sessions = self.session_manager.list_sessions()
                if not sessions:
                    print("No sessions found.")
                else:
                    print("Available Sessions:") # Removed leading \\n
                    for s in sessions:
                        print(f"  ID: {s['id']}, Created: {s.get('created_at', 'N/A')}, Modified: {s.get('last_modified', 'N/A')}, Messages: {s.get('message_count', 0)}")
                    print("-" * 30)
            elif sub_command == "delete":
                if len(args) > 1:
                    self.session_manager.delete_session(args[1])
                else:
                    print("Usage: /chat delete <session_id>")
            elif sub_command == "current":
                session_id = self.session_manager.get_current_session_id()
                if session_id:
                    metadata = self.session_manager.get_current_session_metadata()
                    print(f"\\nCurrent Session ID: {session_id}")
                    print("  Metadata:")
                    for key, value in metadata.items():
                        print(f"    {key}: {value}")
                    print("-" * 30)
                else:
                    print("No active session.")
            elif sub_command == "rename": # New sub-command for /chat
                if len(args) > 1:
                    new_name = args[1]
                    current_id = self.session_manager.get_current_session_id()
                    if not current_id:
                        print("Error: No active session to rename.")
                    elif not new_name.strip():
                        print("Error: New session name cannot be empty.")
                    else:
                        if self.session_manager.rename_session(current_id, new_name.strip()):
                            print(f"Session '{current_id}' renamed to '{new_name.strip()}'.")
                        # Error messages handled by rename_session or if it returns False without specific print
                else:
                    print("Usage: /chat rename <new_name>")
            else:
                print(f"Unknown chat command: /chat {sub_command}. Type /help for available commands.")
                
        elif command == "/think":
            if not args:
                print("Usage: /think <show|hide>")
            elif args[0].lower() == "show":
                self.show_thoughts = True
                print("AI thought process will now be shown.")
            elif args[0].lower() == "hide":
                self.show_thoughts = False
                print("AI thought process will now be hidden.")
            else:
                print("Usage: /think <show|hide>")

        elif command == "/help":
            self._print_help()
        elif command in ["/exit", "/quit"]:
            return True # Signal to exit
        else:
            print(f"Unknown command: {command}. Type /help for available commands.")
        return False # Signal not to exit

    def _print_info(self):
        print("\n--- Connection & Model Information ---")
        print(f"  Endpoint: {self.llm_client.endpoint}")
        print(f"  Model: {self.llm_client.model}")
        
        current_params = self.llm_client.get_all_parameters()
        default_params = self.llm_client.default_params

        print("\n--- System Prompt ---")
        if current_params["system_prompt"]:
            print(f'  "{current_params["system_prompt"]}"')
        else:
            print("  Not set.")

        print("\n--- Custom Parameters (Non-Default) ---")
        has_custom_params = False
        for key, current_value in current_params.items():
            if key == "system_prompt": continue
            if key in default_params and current_value != default_params[key]:
                print(f"  {key}: {current_value} (Default: {default_params[key]})")
                has_custom_params = True
            elif key not in default_params and current_value is not None:
                print(f"  {key}: {current_value}")
                has_custom_params = True
        
        if not has_custom_params:
            print("  All parameters are at their default values.")
        print("-" * 30)

    def start_chat(self):
        """
        Starts the interactive chat loop.
        """
        # Load last session or start a new one
        if not self.session_manager.load_session(): 
            pass # A session (either loaded or new) is now active.

        while True:
            try:
                user_input = input().strip() # Removed "You: " prefix and color
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if self._handle_command(user_input):
                        break # Exit command was issued
                    continue

                # Add user message to session history
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
                                print(chunk, end="", flush=True)
                                accumulated_streamed_content.append(chunk)
                        except Exception as e: # Catch potential errors during streaming iteration
                            print(colorama.Fore.RED + f"\\nError during streaming: {e}" + colorama.Style.RESET_ALL)
                            accumulated_streamed_content.append(f"Error: Stream interrupted: {e}")
                        finally:
                            print() # Ensure a newline after streaming, even if it errors or is empty
                    raw_llm_response = "".join(accumulated_streamed_content)
                    
                    if not raw_llm_response: # If stream produced nothing or response_stream was problematic
                        if response_stream is None: # Check if stream_chat_message itself failed to return a generator
                             raw_llm_response = "Error: Failed to initiate stream with LLM."
                        # else: Stream might have been valid but empty, raw_llm_response remains empty string
                        # This will be handled by the error check or empty string check later

                else: # Not streaming
                    raw_llm_response = self.llm_client.send_chat_message_full_history(messages_for_api)
                    if raw_llm_response is None: 
                        raw_llm_response = "Error: No response from LLM."

                # Process raw_llm_response
                # final_response_to_save = raw_llm_response # This was the old variable name
                # final_response_to_display = raw_llm_response # This was the old variable name

                final_response_to_save_in_history = raw_llm_response # Save raw response to history

                if raw_llm_response and not raw_llm_response.startswith("Error:"):
                    if self.show_thoughts:
                        # Replace <think>content</think> with styled "Thinking: content"
                        # Adding a space after the styled thought for better readability if text follows.
                        final_response_to_display = re.sub(r"<think>(.*?)</think>", 
                                                           lambda m: colorama.Fore.LIGHTBLACK_EX + "Thinking: " + m.group(1).strip() + colorama.Style.RESET_ALL + " ", 
                                                           raw_llm_response, flags=re.DOTALL).strip()
                    else:
                        # Strip <think>content</think> entirely
                        final_response_to_display = re.sub(r"<think>.*?</think>", "", raw_llm_response, flags=re.DOTALL).strip()
                    
                    if final_response_to_save_in_history: # If not empty after potential stripping (for saving)
                        self.session_manager.add_message_to_history("assistant", final_response_to_save_in_history) # Save the raw response
                        
                    # Display logic
                    if not self.llm_client.stream: # If not streaming, print the final_response_to_display
                        if final_response_to_display:
                            print(final_response_to_display)
                        # If it became empty after stripping and not streaming, print nothing extra, 
                        # as the newline is handled by the input loop or stream completion.
                        # else: 
                        #     print() 
                
                elif raw_llm_response: # This means it's an error string from raw_llm_response
                    # Errors from streaming are already printed. This handles non-streaming errors or stream init errors.
                    if not self.llm_client.stream or (self.llm_client.stream and not accumulated_streamed_content):
                         print(colorama.Fore.RED + raw_llm_response + colorama.Style.RESET_ALL)
                
            except KeyboardInterrupt:
                print("\nExiting chat. Goodbye!")
                break
            except Exception as e:
                print(colorama.Fore.RED + f"An error occurred: {e}" + colorama.Style.RESET_ALL)
                # Optionally, decide if you want to break the loop on other exceptions
                # break
