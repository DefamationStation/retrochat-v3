# To keep this file focused and maintainable, try to avoid adding new functions here.
# If additional functionality is needed, consider creating a new module in this directory and importing it.
import json
import os
import uuid
from datetime import datetime
import logging # Added import

from retrochat_app.core.config_manager import SESSIONS_DIR, LAST_SESSION_FILE
# from retrochat_app.core.text_processing_utils import _process_text_for_code_blocks # Removed import
from retrochat_app.core.code_block_utils import process_and_assign_code_block_ids # MODIFIED: Use centralized function
from retrochat_app.core.io_utils import read_json_file, write_json_file # Added import

class SessionManager:
    """
    Manages chat sessions, including loading, saving, creating new sessions,
    and handling persistent code block IDs using centralized utilities.
    """
    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        self.last_session_file = LAST_SESSION_FILE
        self.current_session_id = None
        # Initialize with new fields for code blocks
        self.current_session_data = {
            "conversation_history": [],
            "metadata": {},
            "code_blocks": {}, # {global_id_str: code_content}
            "next_code_block_global_id": 1
        }
        os.makedirs(self.sessions_dir, exist_ok=True)

    def get_session_filepath(self, session_id: str) -> str:
        """Returns the filepath for a given session ID."""
        return os.path.join(self.sessions_dir, f"session_{session_id}.json")

    def _save_last_session_id(self):
        """Saves the current session ID as the last active session."""
        if self.current_session_id is None:
            # If there's no current session ID (e.g., after deleting the last active session and not starting a new one)
            # We can either clear the last_session_file or leave it as is.
            # Clearing it means no session will be auto-loaded next time if no new one is made.
            # For now, let's clear it to avoid loading a non-existent session.
            if os.path.exists(self.last_session_file):
                try:
                    os.remove(self.last_session_file)
                except OSError as e:
                    # from retrochat_app.ui.display_handler import log_error, Console # Removed import
                    # log_error(Console(), f"Error removing last session ID file: {e}") # Removed UI call
                    logging.error(f"Error removing last session ID file: {e}") # Added logging
            return

        try:
            # Use a simple text write, not JSON for this specific file
            with open(self.last_session_file, 'w') as f:
                f.write(self.current_session_id)
        except IOError as e:
            # from retrochat_app.ui.display_handler import log_error, Console # Removed import
            # log_error(Console(), f"Error saving last session ID: {e}") # Removed UI call
            logging.error(f"Error saving last session ID: {e}") # Added logging

    def _load_last_session_id(self) -> str | None:
        """Loads the ID of the last active session."""
        if os.path.exists(self.last_session_file):
            try:
                # Use a simple text read, not JSON for this specific file
                with open(self.last_session_file, 'r') as f:
                    return f.read().strip()
            except IOError as e:
                # from retrochat_app.ui.display_handler import log_error, Console # Removed import
                # log_error(Console(), f"Error loading last session ID: {e}") # Removed UI call
                logging.error(f"Error loading last session ID: {e}") # Added logging
        return None

    def load_session(self, session_id: str | None = None) -> bool:
        """
        Loads a session by ID. If no ID is provided, tries to load the last active session.
        Initializes code block fields if loading an older session format.
        Returns True if a session was successfully loaded, False otherwise.
        """
        if session_id is None:
            session_id = self._load_last_session_id()

        if session_id:
            filepath = self.get_session_filepath(session_id)
            loaded_data = read_json_file(filepath) # Use io_utils

            if loaded_data is not None:
                self.current_session_data = loaded_data
                self.current_session_id = session_id

                # Ensure new fields exist for backward compatibility
                if "code_blocks" not in self.current_session_data:
                    self.current_session_data["code_blocks"] = {}
                if "next_code_block_global_id" not in self.current_session_data:
                    self.current_session_data["next_code_block_global_id"] = 1
                    # No longer re-processing history here, as the new function handles ID assignment
                    # during message addition or if a specific utility is called to re-process.

                self._save_last_session_id() # Update last session on successful load
                return True
            else: # read_json_file returned None, indicating an error
                # Error is already logged by read_json_file
                # If loading fails, start a new session
                self.new_session(f"corrupted_session_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                return False # Indicate that the intended session wasn't loaded

        # If no session_id or loading failed, start a new one
        if not self.current_session_id:
             self.new_session()
        return False

    # Removed _reprocess_history_for_code_blocks as this logic is now part of process_and_assign_code_block_ids
    # or would be a separate utility if needed for bulk reprocessing.

    def save_session(self):
        """Saves the current session data (including code blocks) to a file."""
        if not self.current_session_id:
            return

        filepath = self.get_session_filepath(self.current_session_id)
        self.current_session_data.setdefault("metadata", {})
        self.current_session_data["metadata"]["last_modified"] = datetime.now().isoformat()

        if write_json_file(filepath, self.current_session_data): # Use io_utils
            self._save_last_session_id()
        # else: Error is logged by write_json_file

    def new_session(self, session_id: str | None = None, metadata: dict | None = None) -> str:
        """Creates a new session, optionally with a specific ID and metadata."""
        if self.current_session_id:
            self.save_session()

        self.current_session_id = session_id if session_id else str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Reset session data for the new session
        self.current_session_data = {
            "conversation_history": [],
            "metadata": {
                "created_at": timestamp.isoformat(),
                "name": metadata.get("name") if metadata and "name" in metadata else f"Chat Session {timestamp.strftime('%Y-%m-%d %H:%M')}"
            },
            "code_blocks": {}, # Reset code blocks
            "next_code_block_global_id": 1 # Reset ID counter
        }
        
        filepath = self.get_session_filepath(self.current_session_id)
        if write_json_file(filepath, self.current_session_data): # Use io_utils
            self._save_last_session_id()
        # else: Error is logged by write_json_file
        
        return self.current_session_id

    def add_message_to_history(self, role: str, content: str) -> str:
        """
        Adds a message to the history and returns the stored content.

        Assistant messages are processed for code blocks using the centralized
        utility which assigns global IDs, stores them in ``session_data`` and
        embeds ID tags. The processed content (with embedded IDs) is returned so
        callers can display the exact text that was stored.
        """

        stored_content = content

        if role == "assistant":
            # Use the centralized function. It updates ``self.current_session_data`` directly.
            processed_content, _ = process_and_assign_code_block_ids(
                content,
                self.current_session_data  # Pass the whole session_data dict
            )
            stored_content = processed_content

            # new_blocks are already updated in ``self.current_session_data['code_blocks']``
            # ``next_code_block_global_id`` is also updated by the utility
            self.current_session_data.setdefault("conversation_history", []).append(
                {"role": role, "content": processed_content}
            )
        else:  # User messages or system messages
            self.current_session_data.setdefault("conversation_history", []).append(
                {"role": role, "content": content}
            )

        # Auto-save after each message
        try:
            self.save_session()
        except Exception as e:
            logging.error(f"Failed to save session after adding message: {e}")

        return stored_content

    def get_current_session_history(self) -> list:
        """Returns the conversation history of the current session."""
        return self.current_session_data.get("conversation_history", [])

    def get_current_session_metadata(self) -> dict:
        """Returns the metadata of the current session."""
        return self.current_session_data.get("metadata", {})

    def get_all_sessions(self) -> list[dict]:
        """Lists all available sessions with their ID, name, and last modified date."""
        sessions = []
        for filename in os.listdir(self.sessions_dir):
            if filename.startswith("session_") and filename.endswith(".json"):
                session_id = filename[len("session_"):-len(".json")]
                filepath = self.get_session_filepath(session_id)
                data = read_json_file(filepath) # Use io_utils
                if data:
                    metadata = data.get("metadata", {})
                    sessions.append({
                        "id": session_id,
                        "name": metadata.get("name", "Unnamed Session"),
                        "last_modified": metadata.get("last_modified", "N/A")
                    })
        # Sort sessions by last_modified date, most recent first
        sessions.sort(key=lambda s: s.get("last_modified", ""), reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session by its ID."""
        filepath = self.get_session_filepath(session_id)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logging.info(f"Session {session_id} deleted successfully.") # Added logging
                # If the deleted session was the last active one, clear the last_session_file
                if self._load_last_session_id() == session_id:
                    self.current_session_id = None # Clear current if it was the one deleted
                    self._save_last_session_id() # This will now remove or clear the file
                return True
            except OSError as e:
                # from retrochat_app.ui.display_handler import log_error, Console # Removed import
                # log_error(Console(), f"Error deleting session file {filepath}: {e}") # Removed UI call
                logging.error(f"Error deleting session file {filepath}: {e}") # Added logging
                return False
        else:
            # from retrochat_app.ui.display_handler import log_warning, Console # Removed import
            # log_warning(Console(), f"Session file {filepath} not found for deletion.") # Removed UI call
            logging.warning(f"Session file {filepath} not found for deletion.") # Added logging
            return False

    def rename_session(self, session_id: str, new_name: str) -> bool:
        """Renames a session."""
        filepath = self.get_session_filepath(session_id)
        session_data = read_json_file(filepath) # Use io_utils

        if session_data:
            session_data.setdefault("metadata", {})
            session_data["metadata"]["name"] = new_name
            if write_json_file(filepath, session_data): # Use io_utils
                logging.info(f"Session {session_id} renamed to '{new_name}'.") # Added logging
                # If the renamed session is the current one, update its data in memory too
                if self.current_session_id == session_id:
                    self.current_session_data["metadata"]["name"] = new_name
                return True
            # else: Error is logged by write_json_file
        return False

    # --- Code Block Management ---

    def get_code_block(self, global_id_str: str) -> str | None:
        """Retrieves code content by its global string ID."""
        return self.current_session_data.get("code_blocks", {}).get(global_id_str)

    def get_conversation_history(self, num_messages: int | None = None) -> list[dict[str, str]]: # Restored optional num_messages
        """Returns the conversation history of the current session."""
        history = self.current_session_data.get("conversation_history", [])
        if num_messages is not None:
            history = history[-num_messages:]
        return history

    def clear_current_session_history(self):
        """Clears the conversation history, code blocks, and resets code block ID counter for the current session."""
        if self.current_session_id:
            self.current_session_data["conversation_history"] = []
            self.current_session_data["code_blocks"] = {}
            self.current_session_data["next_code_block_global_id"] = 1
            self.save_session()
            # from retrochat_app.ui.display_handler import log_error, Console # Removed import
            # Print handled by UI, not here
        else:
            # from retrochat_app.ui.display_handler import log_error, Console # Removed import
            # log_error(Console(), "No active session to clear.") # Removed UI call
            logging.warning("No active session to clear.") # Added logging
