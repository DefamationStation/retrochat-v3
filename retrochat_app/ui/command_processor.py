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
            param_name, value = args[0], args[1]
            if param_name.lower() == "stream":
                if value.lower() == "true": ui.llm_client.set_parameter(param_name, True)
                elif value.lower() == "false": ui.llm_client.set_parameter(param_name, False)
                else: ui.console.print("[red]Invalid value for stream. Use 'true' or 'false'.[/red]")
            elif param_name.lower() == "endpoint":
                # Validate and update the endpoint
                if ":" not in value or not value.replace(".", "").replace(":", "").isdigit():
                    ui.console.print("[red]Invalid endpoint format. Expected IP:PORT (e.g., 192.168.1.82:1234).[/red]")
                else:
                    # value is now just "ip:port"
                    update_api_base_url(value) # Pass "ip:port" directly
                    ui.llm_client.update_endpoint()
                    # CHAT_COMPLETIONS_ENDPOINT is updated in config_manager and llm_client will pick it up
                    ui.console.print(f"[green]API endpoint updated. Current completions endpoint: {ui.llm_client.endpoint}[/green]")
            else:
                ui.llm_client.set_parameter(param_name, value)
        else:
            ui.console.print("Usage: /set <param_name> <value>")
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
    elif command == "/stream":
        if len(args) == 1 and args[0].lower() in {"true", "false"}:
            ui.llm_client.set_parameter("stream", args[0].lower()) # Use set_parameter to save
        else:
            ui.console.print("[cyan]Usage: /stream true|false[/cyan]")
        return False
    elif command == "/history":
        history = ui.session_manager.get_conversation_history()
        if not history: ui.console.print("Conversation history is empty for the current session.")
        else:
            ui.console.print("\\\\nConversation History:")
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
            ui.code_block_formatter.reset() # Reset formatter
        elif sub_command == "new":
            new_session_id = args[1] if len(args) > 1 else None
            ui.session_manager.new_session(new_session_id)
            ui.code_block_formatter.reset() # Reset formatter
            ui.console.print(f"Started new session: {ui.session_manager.get_current_session_id()}")
        elif sub_command == "load":
            if len(args) > 1:
                session_to_load = args[1]
                if ui.session_manager.load_session(session_to_load):
                    ui.code_block_formatter.reset() # Reset formatter
                    # ui.console.print(f"Session '{session_to_load}' loaded.") # load_session handles messages
                    # When loading a session, we might want to re-process and display its history
                    # For now, just resetting the formatter. Displaying history would require
                    # iterating through loaded history and calling formatter.
            else:
                ui.console.print("Usage: /chat load <session_id>")
        elif sub_command == "list":
            sessions = ui.session_manager.list_sessions()
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
            session_id = ui.session_manager.get_current_session_id()
            if session_id:
                metadata = ui.session_manager.get_current_session_metadata()
                ui.console.print(f"\\\\nCurrent Session ID: {session_id}")
                ui.console.print("  Metadata:")
                for key, value in metadata.items():
                    ui.console.print(f"    {key}: {value}")
                ui.console.print("-" * 30)
            else:
                ui.console.print("No active session.")
        elif sub_command == "rename": 
            if len(args) > 1:
                new_name = args[1]
                current_id = ui.session_manager.get_current_session_id()
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
