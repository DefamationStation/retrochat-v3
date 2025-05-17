"""
Handles terminal-based user interface for the chat application.
"""
# Adjusted import path for LLMClient
from retrochat_app.api.llm_client import LLMClient
import shlex # For parsing command arguments

class TerminalUI:
    """
    Manages the chat interface in the terminal.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.conversation_history = []

    def _print_help(self):
        print("\nAvailable commands:")
        print("  /help                          - Show this help message.")
        print("  /info                          - Show connection info, system prompt, and non-default parameters.")
        print("  /set <param> <value>           - Set a model parameter (e.g., /set temperature 0.5).")
        print("                                   Available params: model, temperature, max_tokens, top_p, presence_penalty, frequency_penalty, stream.")
        print('  /system <prompt>               - Set the system prompt (e.g., /system "You are a helpful assistant.").')
        print("  /system clear                  - Clear the system prompt.")
        print('  /addstop <sequence>            - Add a stop sequence (e.g., /addstop "User:").')
        print("  /rmstop <sequence>             - Remove a stop sequence.")
        print("  /clearstops                    - Clear all stop sequences.")
        print("  /params                        - Show current model parameters and system prompt.")
        print("  /history                       - Show the current conversation history.")
        print("  /clearhistory                  - Clear the current conversation history.")
        print("  /exit or /quit                 - Exit the chat.")
        print("-" * 30)

    def _handle_command(self, command_input: str):
        try:
            parts = shlex.split(command_input)
        except ValueError as e:
            print(f"Error parsing command: {e}. Ensure quotes are properly matched.")
            return False # Indicate command processing failed or no exit needed

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
        elif command == "/addstop":
            if len(args) == 1: self.llm_client.add_stop_sequence(args[0])
            else: print("Usage: /addstop <sequence>")
        elif command == "/rmstop":
            if len(args) == 1: self.llm_client.remove_stop_sequence(args[0])
            else: print("Usage: /rmstop <sequence>")
        elif command == "/clearstops":
            self.llm_client.clear_stop_sequences()
        elif command == "/params":
            params = self.llm_client.get_all_parameters()
            print("\nCurrent Parameters:")
            for key, value in params.items():
                if key == "system_prompt" and value is None: print(f"  {key}: Not set")
                elif key == "system_prompt": print(f'  {key}: "{value}"')
                else: print(f"  {key}: {value}")
            print("-" * 30)
        elif command == "/history":
            if not self.conversation_history: print("Conversation history is empty.")
            else:
                print("\nConversation History:")
                for msg in self.conversation_history:
                    print(f"  {msg['role'].capitalize()}: {msg['content']}")
                print("-" * 30)
        elif command == "/clearhistory":
            self.conversation_history = []
            print("Conversation history cleared.")
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
        print("RetroChat connected. Type /help for commands, or start chatting.")
        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input: continue

                if user_input.startswith("/"):
                    if self._handle_command(user_input): break
                    continue
                
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting chat. Goodbye!")
                    break
                
                assistant_response = self.llm_client.send_chat_message(user_input, self.conversation_history)

                if assistant_response:
                    print(f"LLM: {assistant_response}")
                    self.conversation_history.append({"role": "user", "content": user_input})
                    self.conversation_history.append({"role": "assistant", "content": assistant_response})
                else:
                    print("LLM: I encountered an error or received no response. Please try again.")
            except KeyboardInterrupt:
                print("\nExiting chat. Goodbye!")
                break
            except Exception as e:
                print(f"An unexpected error occurred in the chat loop: {e}")
