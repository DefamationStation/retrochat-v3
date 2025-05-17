"""
Main entry point for the LM Studio Chat Application.
"""
# Adjusted import paths
from retrochat_app.api.llm_client import LLMClient
from retrochat_app.ui.terminal_ui import TerminalUI
from retrochat_app.core.config_manager import API_BASE_URL # For checking if config is loaded

def main():
    """
    Initializes and starts the chat application.
    """
    print(f"Application starting...")
    # print(f"Attempting to connect to LM Studio at: {API_BASE_URL}") # Less verbose startup

    llm_client = LLMClient()
    ui = TerminalUI(llm_client)
    ui.start_chat()

if __name__ == "__main__":
    main()
