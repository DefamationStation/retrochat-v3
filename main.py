"""
Main entry point for the LM Studio Chat Application.
"""
# Ensure logger is set up at the very beginning
from retrochat_app.utils import logger_setup # Import logger_setup first
import logging # Import logging to get a logger instance if needed here

# Adjusted import paths
from retrochat_app.api.llm_client import LLMClient
from retrochat_app.ui.terminal_ui import TerminalUI
from retrochat_app.core.session_manager import SessionManager # Import SessionManager
from retrochat_app.core.config_manager import API_BASE_URL # For checking if config is loaded

def main():
    """
    Initializes and starts the chat application.
    """
    main_logger = logging.getLogger(__name__) # Get a logger for main
    main_logger.info("Application starting...")
    try:
        llm_client = LLMClient()
        session_manager = SessionManager() # Instantiate SessionManager
        ui = TerminalUI(llm_client, session_manager) # Pass session_manager to TerminalUI
        ui.run() # Changed from ui.start_chat() to ui.run()
    except Exception as e:
        main_logger.exception("Unhandled exception in main:")
        # print(f"An unexpected error occurred in main: {e}") # Commented out console print
    finally:
        main_logger.info("Application shutting down...")
        logging.shutdown() # Ensure logs are flushed
        # print("[Main] Application shutdown sequence complete. Log flushing attempted.") # Commented out console print


if __name__ == "__main__":
    # setup_logging() is called when logger_setup is imported
    main()
