\
"""
Handles display-related functionalities for the terminal UI.
"""
from rich.console import Console
from rich.markdown import Markdown

def log_error(console: Console, message: str):
    """Centralized error logging for the UI."""
    console.print(f"[red][ERROR][/red] {message}")

def show_help(console: Console):
    """Prints the help message to the console."""
    console.print("Available commands:")
    console.print("  /help                          - Show this help message.")
    console.print("  /info                          - Show connection info, system prompt, and non-default parameters.")
    console.print("  /set <param> <value>           - Set a model parameter (e.g., /set temperature 0.5).")
    console.print("                                   Available params: model, temperature, max_tokens, top_p, presence_penalty, frequency_penalty, stream.")
    console.print('  /system <prompt>               - Set the system prompt (e.g., /system "You are a helpful assistant.").')
    console.print("  /system clear                  - Clear the system prompt.")
    console.print("  /params                        - Show current model parameters and system prompt.")
    console.print("  /history                       - Show the current conversation history for the active session.")
    console.print("  /chat reset                    - Clear the current conversation history for the active session.")
    console.print("  /chat new [id]                 - Start a new chat session (optional id).")
    console.print("  /chat load <session_id>        - Load a specific chat session.")
    console.print("  /chat list                     - List all available chat sessions.")
    console.print("  /chat delete <session_id>      - Delete a specific chat session.")
    console.print("  /chat rename <new_name>        - Rename the current active chat session.")
    console.print("  /chat current                  - Show the current session ID and metadata.")
    console.print("  /stream true/false             - Enable or disable streaming responses.")
    console.print("  /think show                    - Show AI thought process (styled, no tags).")
    console.print("  /think hide                    - Hide AI thought process.")
    console.print("  /copy <CodeID>                 - Copy the content of a specific code block to clipboard.")
    console.print("  /exit or /quit                 - Exit the chat.")
    console.print("-" * 30)

def show_system_info(console: Console, llm_client):
    """Prints connection, model, system prompt, and custom parameters."""
    console.print("\n--- Connection & Model Information ---")
    console.print(f"  Endpoint: {llm_client.endpoint}")
    console.print(f"  Model: {llm_client.model}")

    current_params = llm_client.get_all_parameters()
    
    # Import config_manager to get default settings
    from retrochat_app.core import config_manager
    default_params = config_manager.get_default_settings()

    console.print("\n--- System Prompt ---")
    if current_params["system_prompt"]:
        console.print(f'  "{current_params["system_prompt"]}"')
    else:
        console.print("  Not set.")

    console.print("\n--- Custom Parameters (Non-Default) ---")
    has_custom_params = False
    for key, current_value in current_params.items():
        if key == "system_prompt":
            continue
        if key in default_params and current_value != default_params[key]:
            console.print(f"  {key}: {current_value} (Default: {default_params[key]})")
            has_custom_params = True
        elif key not in default_params and current_value is not None:
            console.print(f"  {key}: {current_value}")
            has_custom_params = True

    if not has_custom_params:
        console.print("  All parameters are at their default values.")
    console.print("-" * 30)

def render_message(console: Console, role: str, text: str, is_error: bool = False, is_thought: bool = False, show_thoughts_flag: bool = False):
    """
    Displays a message in the terminal, applying styles based on the role.
    """
    if is_error:
        console.print(f"[red]{text}[/red]")
    elif is_thought:
        if show_thoughts_flag:
            console.print(f"[dim italic]Thought: {text}[/dim italic]")
    elif role == "user":
        console.print(Markdown(text), style="green")
    elif role == "assistant":
        console.print(Markdown(text), style="yellow")
    else: # System messages or other roles
        console.print(text)
