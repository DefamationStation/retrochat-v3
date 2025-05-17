\
import json
import os
import uuid
from datetime import datetime

from retrochat_app.core.config_manager import SESSIONS_DIR, LAST_SESSION_FILE

class SessionManager:
    """
    Manages chat sessions, including loading, saving, and creating new sessions.
    """
    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        self.last_session_file = LAST_SESSION_FILE
        self.current_session_id = None
        self.current_session_data = {"conversation_history": [], "metadata": {}}
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
                    print(f"Error removing last session ID file: {e}")
            return

        try:
            with open(self.last_session_file, 'w') as f:
                f.write(self.current_session_id)
        except IOError as e:
            print(f"Error saving last session ID: {e}")

    def _load_last_session_id(self) -> str | None:
        """Loads the ID of the last active session."""
        if os.path.exists(self.last_session_file):
            try:
                with open(self.last_session_file, 'r') as f:
                    return f.read().strip()
            except IOError as e:
                print(f"Error loading last session ID: {e}")
        return None

    def load_session(self, session_id: str | None = None) -> bool:
        """
        Loads a session by ID. If no ID is provided, tries to load the last active session.
        Returns True if a session was successfully loaded, False otherwise.
        """
        if session_id is None:
            session_id = self._load_last_session_id()

        if session_id:
            filepath = self.get_session_filepath(session_id)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        self.current_session_data = json.load(f)
                        self.current_session_id = session_id
                        self._save_last_session_id() # Update last session on successful load
                        return True
                except (IOError, json.JSONDecodeError) as e:
                    print(f"Error loading session {session_id} from {filepath}: {e}")
                    # If loading fails, start a new session
                    self.new_session(f"corrupted_session_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    return False # Indicate that the intended session wasn't loaded
        # If no session_id or loading failed, start a new one
        if not self.current_session_id: # Ensure new_session is only called if no session is loaded
             self.new_session() # Start a new session if no previous one or load failed
        return False # No specific session loaded, new one started by new_session()

    def save_session(self):
        """Saves the current session data to a file."""
        if not self.current_session_id:
            print("No active session to save.")
            return

        filepath = self.get_session_filepath(self.current_session_id)
        try:
            # Update last modified timestamp
            self.current_session_data.setdefault("metadata", {})
            self.current_session_data["metadata"]["last_modified"] = datetime.now().isoformat()

            with open(filepath, 'w') as f:
                json.dump(self.current_session_data, f, indent=4)
            self._save_last_session_id()
            # print(f"Session '{self.current_session_id}' saved.") # Optional: for verbose logging
        except IOError as e:
            print(f"Error saving session {self.current_session_id} to {filepath}: {e}")
        except TypeError as e:
            print(f"Error serializing session data for {self.current_session_id}: {e}")


    def new_session(self, session_id: str | None = None):
        """
        Starts a new chat session. If session_id is provided, it uses that;
        otherwise, it generates a new unique ID.
        """
        if session_id is None:
            self.current_session_id = str(uuid.uuid4())
        else:
            self.current_session_id = session_id

        self.current_session_data = {
            "conversation_history": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "session_id": self.current_session_id
            }
        }
        self.save_session() # Save the new session immediately

    def add_message_to_history(self, role: str, content: str):
        """Adds a message to the current session's conversation history and saves the session."""
        if not self.current_session_id:
            print("No active session. Cannot add message.")
            # Optionally, start a new session here if desired behavior
            # self.new_session()
            # print("Started a new session to add the message.")
            return

        self.current_session_data["conversation_history"].append({"role": role, "content": content})
        self.save_session()

    def get_conversation_history(self) -> list:
        """Returns the conversation history of the current session."""
        return self.current_session_data.get("conversation_history", [])

    def clear_current_session_history(self):
        """Clears the conversation history of the current session and saves."""
        if self.current_session_id:
            self.current_session_data["conversation_history"] = []
            self.current_session_data["metadata"]["history_cleared_at"] = datetime.now().isoformat()
            self.save_session()
            print(f"Conversation history for session '{self.current_session_id}' cleared.")
        else:
            print("No active session to clear.")

    def list_sessions(self) -> list[dict]:
        """Lists all available sessions with their ID and last modified time."""
        sessions = []
        for filename in os.listdir(self.sessions_dir):
            if filename.startswith("session_") and filename.endswith(".json"):
                session_id = filename[len("session_"):-len(".json")]
                filepath = self.get_session_filepath(session_id)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        metadata = data.get("metadata", {})
                        last_modified = metadata.get("last_modified", "N/A")
                        created_at = metadata.get("created_at", "N/A")
                        sessions.append({
                            "id": session_id,
                            "created_at": created_at,
                            "last_modified": last_modified,
                            "message_count": len(data.get("conversation_history", []))
                        })
                except (IOError, json.JSONDecodeError) as e:
                    print(f"Error reading session file {filename}: {e}")
        # Sort sessions by last_modified time, most recent first
        sessions.sort(key=lambda s: s.get("last_modified", "0"), reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session by its ID."""
        filepath = self.get_session_filepath(session_id)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Session '{session_id}' deleted.")
                # If the deleted session was the last active one, clear the last_session_file
                if self._load_last_session_id() == session_id:
                    if os.path.exists(self.last_session_file):
                        os.remove(self.last_session_file)
                    self.current_session_id = None # Clear current session if it was deleted
                    self.current_session_data = {"conversation_history": [], "metadata": {}}
                return True
            except OSError as e:
                print(f"Error deleting session file {filepath}: {e}")
                return False
        else:
            print(f"Session '{session_id}' not found.")
            return False

    def get_current_session_id(self) -> str | None:
        """Returns the ID of the currently active session."""
        return self.current_session_id

    def get_current_session_metadata(self) -> dict:
        """Returns the metadata of the current session."""
        return self.current_session_data.get("metadata", {})

    def rename_session(self, old_session_id: str, new_session_id: str) -> bool:
        """
        Renames a session. This involves renaming the session file and updating metadata.
        Returns True if successful, False otherwise.
        """
        if not old_session_id or not new_session_id:
            print("Error: Both old and new session IDs must be provided for renaming.")
            return False
        
        if old_session_id == new_session_id:
            print("Error: New session name is the same as the old one.")
            return False

        old_filepath = self.get_session_filepath(old_session_id)
        new_filepath = self.get_session_filepath(new_session_id)

        if not os.path.exists(old_filepath):
            print(f"Error: Session '{old_session_id}' not found.")
            return False

        if os.path.exists(new_filepath):
            print(f"Error: A session with the name '{new_session_id}' already exists. Please choose a unique name.")
            return False

        try:
            # Load the session data to update metadata
            with open(old_filepath, 'r') as f:
                session_data = json.load(f)
            
            # Update metadata
            session_data.setdefault("metadata", {})
            session_data["metadata"]["session_id"] = new_session_id # Update the ID in metadata
            session_data["metadata"]["previous_session_id"] = old_session_id
            session_data["metadata"]["renamed_at"] = datetime.now().isoformat()

            # Write to new file first
            with open(new_filepath, 'w') as f:
                json.dump(session_data, f, indent=4)
            
            # Remove old file
            os.remove(old_filepath)

            # If the renamed session was the current active session, update current_session_id
            if self.current_session_id == old_session_id:
                self.current_session_id = new_session_id
                self.current_session_data = session_data # Update in-memory data as well
                self._save_last_session_id() # Update last session ID to the new ID
            
            # If the renamed session was the one in .last_session, update that file too
            # (This is covered by the above block if it was the current session)
            # However, if it wasn't the *current* active one but *was* the last loaded one, 
            # we should still update .last_session if it pointed to old_id.
            last_loaded_id = self._load_last_session_id()
            if last_loaded_id == old_session_id and self.current_session_id != new_session_id:
                # This case is tricky: if current session is X, and we rename last_session Y to Z.
                # We should update .last_session to Z if Y was indeed the last one.
                # The _save_last_session_id() called when current_session_id is updated handles the main case.
                # For safety, if the current session is NOT the one being renamed, but the one being renamed
                # IS the last_session_id, we should update the last_session_file to point to the new_session_id.
                # However, self.current_session_id is already updated if it was the active one.
                # The _save_last_session_id() uses self.current_session_id. So this should be fine.
                pass # The logic for updating current_session_id and then _save_last_session_id() should cover this.

            return True
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"Error renaming session '{old_session_id}' to '{new_session_id}': {e}")
            # Attempt to clean up new file if old one still exists and new one was created
            if os.path.exists(new_filepath) and not os.path.exists(old_filepath):
                try:
                    os.remove(new_filepath)
                    print(f"Cleaned up partially created session file: {new_filepath}")
                except OSError as cleanup_e:
                    print(f"Error during cleanup of {new_filepath}: {cleanup_e}")
            return False
