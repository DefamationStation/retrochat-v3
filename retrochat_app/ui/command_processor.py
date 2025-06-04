\
"""
Handles command processing for the terminal UI.
"""
import shlex
import pyperclip
# Assuming TerminalUI, LLMClient, SessionManager are complex types,
# using 'typing.Any' for simplicity or forward references if needed.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .terminal_ui import TerminalUI # To avoid circular import at runtime
    from .code_block_formatter import CodeBlockFormatter # For type hint if needed

from retrochat_app.core.config_manager import update_api_base_url # Add this import
from retrochat_app.core import provider_manager

def process_command(ui: 'TerminalUI', command_input: str) -> bool:
    """
    Parses and executes commands.
    Returns True if the command signals to exit, False otherwise.
    """
    try:
        parts = shlex.split(command_input)
    except ValueError as e:
        ui.console.print(f"[red]Error parsing command: {e}. Ensure quotes are properly matched.[/red]")
        return False

    if not parts:
        return False

    command = parts[0].lower()
    args = parts[1:]
    # Provider management commands
    if command == "/provider":
        if not args:
            ui.console.print("Usage: /provider <list|add|edit|delete|select|set-header> [args]")
            return False
        sub = args[0].lower()
        # List providers
        if sub == "list":
            provs, active = provider_manager.list_providers()
            if not provs:
                ui.console.print("No providers configured.")
            else:
                ui.console.print("Configured Providers:")
                for p in provs:
                    mark = "*" if p.get("name") == active else " "
                    ui.console.print(f" {mark} {p.get('name')}")
            return False
        # Add provider
        elif sub == "add":
            if len(args) < 4:
                ui.console.print("Usage: /provider add <name> <type> <api_base_url> [chat_completions_endpoint]")
                return False
            name, typ, base = args[1], args[2], args[3]
            endpoint = args[4] if len(args) >= 5 else None
            success, path = provider_manager.add_provider(name, typ, base, endpoint)
            if success:
                ui.console.print(f"Provider '{name}' added. Edit config at: {path}")
            else:
                ui.console.print(f"[red]Failed to add provider '{name}'[/red]")
            return False
        # Edit provider
        elif sub == "edit":
            if len(args) != 2:
                ui.console.print("Usage: /provider edit <name>")
                return False
            name = args[1]
            if provider_manager.edit_provider(name):
                ui.console.print(f"Provider '{name}' edited successfully.")
            else:
                ui.console.print(f"[red]Failed to edit provider '{name}'[/red]")
            return False
        # Delete provider
        elif sub == "delete":
            if len(args) != 2:
                ui.console.print("Usage: /provider delete <name>")
                return False
            name = args[1]
            if provider_manager.delete_provider(name):
                ui.console.print(f"Provider '{name}' deleted.")
            else:
                ui.console.print(f"[red]Failed to delete provider '{name}'[/red]")
            return False
        # Select provider
        elif sub == "select":
            if len(args) != 2:
                ui.console.print("Usage: /provider select <name>")
                return False
            name = args[1]
            if provider_manager.select_provider(name):
                ui.console.print(f"Provider '{name}' selected as active.")
            else:
                ui.console.print(f"[red]Failed to select provider '{name}'[/red]")
            return False
        elif sub == "set-header":
            if len(args) < 4:
                ui.console.print("Usage: /provider set-header <name> <header_key> <header_value>")
                return False
            name, header_key = args[1], args[2]
            header_value = " ".join(args[3:])
            if provider_manager.set_provider_header(name, header_key, header_value):
                ui.console.print(f"Header '{header_key}' set for provider '{name}'.")
            else:
                ui.console.print(f"[red]Failed to set header for provider '{name}'[/red]")
            return False
        else:
            ui.console.print(f"Unknown provider command: {sub}. Use list, add, edit, delete, select, set-header.")
            return False

    if command == "/info":
        # Assuming show_system_info is now in display_handler and called from ui or passed console and llm_client
        from .display_handler import show_system_info # Local import to use the new function
        show_system_info(ui.console, ui.llm_client)
        return False
    elif command == "/help":
        from .display_handler import show_help # Local import
        show_help(ui.console)
        return False
    elif command == "/set":
        if len(args) == 2:
            param_key, value_str = args[0].lower(), args[1]
            
            if param_key == "ip":
                # Expected value_str: "192.168.1.82:1234" or "http://192.168.1.82:1234"
                if ui.llm_client.set_parameter("api_ip_port", value_str):
                    # Confirmation is printed by llm_client.set_parameter
                    pass
                else:
                    ui.console.print(f"[red]Failed to set API IP/Port.[/red]")
            elif param_key == "endpoint":
                # Expected value_str: "http://192.168.1.82:1234/v1/chat/completions"
                if ui.llm_client.set_parameter("api_full_endpoint", value_str):
                    # Confirmation is printed by llm_client.set_parameter
                    pass
                else:
                    ui.console.print(f"[red]Failed to set API endpoint.[/red]")
            elif param_key == "stream":
                stream_value = value_str.lower() == "true"
                if ui.llm_client.set_parameter("stream", stream_value): # LLMClient should handle type
                    ui.console.print(f"Stream set to: {stream_value}")
                else:
                    ui.console.print(f"[red]Failed to set stream parameter.[/red]")
            else:
                # For other model parameters (temperature, max_tokens, etc.)
                # Try to convert to float or int if applicable, otherwise pass as string
                # LLMClient's set_parameter or config.update_model_parameter should handle final type casting
                try:
                    if '.' in value_str:
                        typed_value = float(value_str)
                    else:
                        typed_value = int(value_str)
                except ValueError:
                    typed_value = value_str # Pass as string if not clearly float/int

                if ui.llm_client.set_parameter(param_key, typed_value):
                    # Confirmation printed by llm_client or its underlying methods
                    pass
                else:
                    ui.console.print(f"[red]Failed to set parameter '{param_key}'.[/red]")
        else:
            ui.console.print("Usage: /set <key> <value>. Use /help for available commands and keys.")
        return False
    elif command == "/system":
        if not args: ui.console.print("Usage: /system <prompt_string> or /system clear")
        elif args[0].lower() == "clear": ui.llm_client.set_system_prompt(None)
        else: ui.llm_client.set_system_prompt(" ".join(args))
        return False
    elif command == "/params":
        params = ui.llm_client.get_all_parameters()
        ui.console.print("Current Parameters:") 
        for key, value in params.items():
            if key == "system_prompt" and value is None: ui.console.print(f"  {key}: Not set")
            elif key == "system_prompt": ui.console.print(f'  {key}: "{value}"')
            else: ui.console.print(f"  {key}: {value}")
        ui.console.print("-" * 30)
        return False
    elif command == "/stream": # This command might become redundant if /set stream true/false is preferred
        if len(args) == 1 and args[0].lower() in {"true", "false"}:
            stream_value = args[0].lower() == "true"
            if ui.llm_client.set_parameter("stream", stream_value): # Use set_parameter to save
                 ui.console.print(f"Stream set to: {stream_value}")
            else:
                ui.console.print(f"[red]Failed to set stream parameter via /stream command.[/red]")
        else:
            ui.console.print("[cyan]Usage: /stream true|false. Consider using /set stream true|false.[/cyan]")
        return False
    elif command == "/history":
        history = ui.session_manager.get_conversation_history()
        if not history: ui.console.print("Conversation history is empty for the current session.")
        else:
            # Display a blank line before the history header
            ui.console.print("\nConversation History:")
            for msg in history:
                ui.console.print(f"  {msg['role'].capitalize()}: {msg['content']}")
            ui.console.print("-" * 30)
        return False
    elif command == "/chat":
        if not args:
            ui.console.print("Usage: /chat <reset|new|load|list|delete|current|rename>")
            return False
        
        sub_command = args[0].lower()
        if sub_command == "reset":
            ui.session_manager.clear_current_session_history() # This method should handle its own print confirmation
            ui.console.print("[green]Chat history and associated code blocks for the current session have been cleared.[/green]")
        elif sub_command == "new":
            new_session_id = args[1] if len(args) > 1 else None
            ui.session_manager.new_session(new_session_id)
            # TODO: TerminalUI's code_block_formatter needs to be re-initialized with the new session_data
            ui.console.print(f"Started new session: {ui.session_manager.current_session_id}")
        elif sub_command == "load":
            if len(args) > 1:
                session_to_load = args[1]
                if ui.session_manager.load_session(session_to_load):
                    # TODO: TerminalUI's code_block_formatter needs to be re-initialized with the new session_data
                    ui.console.print(f"Session '{session_to_load}' loaded.")
                    # Consider calling a method in UI to refresh history display
                else:
                    # If load_session failed and potentially started a recovery session
                    # TODO: TerminalUI's code_block_formatter needs to be re-initialized
                    ui.console.print(f"[yellow]Failed to load session '{session_to_load}'. Active session is now '{ui.session_manager.current_session_id}'.[/yellow]")
            else:
                ui.console.print("Usage: /chat load <session_id>")
        elif sub_command == "list":
            sessions = ui.session_manager.get_all_sessions() # Corrected method name
            if not sessions:
                ui.console.print("No sessions found.")
            else:
                ui.console.print("Available Sessions:")
                for s in sessions:
                    ui.console.print(f"  ID: {s['id']}, Created: {s.get('created_at', 'N/A')}, Modified: {s.get('last_modified', 'N/A')}, Messages: {s.get('message_count', 0)}")
                ui.console.print("-" * 30)
        elif sub_command == "delete":
            if len(args) > 1:
                ui.session_manager.delete_session(args[1])
            else:
                ui.console.print("Usage: /chat delete <session_id>")
        elif sub_command == "current":
            session_id = ui.session_manager.current_session_id # Corrected to direct attribute access
            if session_id:
                metadata = ui.session_manager.get_current_session_metadata()
                ui.console.print(f"\\\\\\\\nCurrent Session ID: {session_id}")
                ui.console.print("  Metadata:")
                for key, value in metadata.items():
                    ui.console.print(f"    {key}: {value}")
                ui.console.print("-" * 30)
            else:
                ui.console.print("No active session.")
        elif sub_command == "rename": 
            if len(args) > 1:
                new_name = args[1]
                current_id = ui.session_manager.current_session_id # Corrected to direct attribute access
                if not current_id:
                    ui.console.print("[red]Error: No active session to rename.[/red]")
                elif not new_name.strip():
                    ui.console.print("[red]Error: New session name cannot be empty.[/red]")
                else:
                    if ui.session_manager.rename_session(current_id, new_name.strip()):
                        ui.console.print(f"Session '{current_id}' renamed to '{new_name.strip()}'.")
            else:
                ui.console.print("Usage: /chat rename <new_name>")
        else:
            ui.console.print(f"[red]Unknown chat command: /chat {sub_command}. Type /help for available commands.[/red]")
            
    elif command == "/think":
        if not args:
            ui.console.print("Usage: /think <show|hide>")
        elif args[0].lower() == "show":
            ui.show_thoughts = True
            ui.console.print("AI thought process will now be shown.")
        elif args[0].lower() == "hide":
            ui.show_thoughts = False
            ui.console.print("AI thought process will now be hidden.")
        else:
            ui.console.print("Usage: /think <show|hide>")
    elif command == "/copy":
        if len(args) == 1:
            block_id_str = args[0]
            # We expect block_id_str to be a numeric string.
            # CodeBlockFormatter.get_code_by_id expects a string.
            # session_data["code_blocks"] keys are strings.
            
            # Validate if block_id_str is a number before passing, but pass as string.
            if not block_id_str.isdigit():
                ui.console.print(f"[red]Invalid Code Block ID: '{block_id_str}'. ID must be a number.[/red]")
                return False # Keep as False, was missing before

            code_content = ui.code_block_formatter.get_code_by_id(block_id_str) # Pass string ID
            
            if code_content is not None:
                try:
                    pyperclip.copy(code_content)
                    ui.console.print(f"Code block [cyan]ID {block_id_str}[/cyan] copied to clipboard.")
                except pyperclip.PyperclipException as e:
                    ui.console.print(f"[red]Error copying to clipboard: {e}. Make sure you have a copy/paste mechanism installed (e.g., xclip or xsel on Linux, or that your environment supports clipboard operations).[/red]")
            else:
                ui.console.print(f"[red]Code block with ID '{block_id_str}' not found or not yet processed by the formatter for the current view.[/red]")
        else:
            ui.console.print("Usage: /copy <CodeID>")
    elif command == "/exit" or command == "/quit":
        return True # Signal to exit
    else:
        ui.console.print(f"[red]Unknown command: {command}. Type /help for available commands.[/red]")
    return False
