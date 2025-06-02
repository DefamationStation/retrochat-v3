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
    console.print("  /set <param> <value>           - Set a model or API parameter.")
    console.print("                                   API params: ip <ip:port_or_full_base_url>, endpoint <full_url>.")
    console.print("                                     e.g., /set ip 192.168.1.82:1234")
    console.print("                                     e.g., /set endpoint http://localhost:5000/custom/api")
    console.print("                                   Model params: model, temperature, max_tokens, top_p, presence_penalty, frequency_penalty, stream (true/false).")
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
    console.print("")
    console.print("Provider management commands:")
    console.print("  /provider list                 - List configured providers.")
    console.print("  /provider add <name> <type> <api_base_url> [chat_endpoint]  - Add a new provider and edit its config.")
    console.print("  /provider edit <name>          - Edit an existing provider's configuration in editor.")
    console.print("  /provider delete <name>        - Delete a provider.")
    console.print("  /provider select <name>        - Select a provider as active.")
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
    # Provider info
    from retrochat_app.core import provider_manager
    provs, active = provider_manager.list_providers()
    console.print("\n--- Providers ---")
    if not provs:
        console.print("  No providers configured. Using defaults.")
    else:
        console.print(f"  Active provider: {active if active else 'None'}")
        console.print("  All providers:")
        for p in provs:
            mark = "*" if p.get('name') == active else " "
            console.print(f"   {mark} {p.get('name')}")
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
