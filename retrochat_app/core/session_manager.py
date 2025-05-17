\
import json
import os
import uuid
from datetime import datetime
import re # Added for code block processing

from retrochat_app.core.config_manager import SESSIONS_DIR, LAST_SESSION_FILE

# Helper function to process markdown for code blocks - can be outside class or static
def _process_text_for_code_blocks(markdown_text: str, starting_id: int) -> tuple[str, dict[str, str], int]:
    """
    Finds code blocks, assigns unique string IDs, stores them, and embeds ID tags in the text.
    The ID tag is placed on the same line as the opening fence.
    Returns:
        - processed_markdown: Markdown text with ID tags embedded.
        - found_blocks: Dictionary of {block_id_str: code_content} for newly found blocks.
        - next_id: The next available global ID.
    """
    found_blocks = {}
    current_global_id = starting_id
    
    # Regex to find fenced code blocks (```optional_lang\\ncode\\n```
    # Captures: group(1)=opening_fence (e.g., ```python\\n), group(2)=code_content, group(3)=closing_fence (e.g., \\n```
    # Updated regex to be more tolerant of whitespace:
    code_block_pattern = re.compile(
        r"^(```\s*(?:[a-zA-Z0-9_\\-]*)\s*(?:\r\n|\n|\r))(.*?)((?:\r\n|\n|\r)```\s*)$", 
        re.MULTILINE | re.DOTALL
    )
    
    processed_text_parts = []
    last_end = 0
    
    for match in code_block_pattern.finditer(markdown_text):
        start_block, end_block = match.span()
        opening_fence = match.group(1) # e.g., ```python\\n
        code_content = match.group(2)  # The actual code
        closing_fence = match.group(3) # e.g., \\n```

        block_id_str = str(current_global_id)
        found_blocks[block_id_str] = code_content
        
        # Add text before this code block
        processed_text_parts.append(markdown_text[last_end:start_block])
        
        # Create the ID tag to be inserted
        # Example: ```python [CodeID: 123]\\n
        # Simplified ID tag for now:
        id_tag_display = f" [CodeID: {block_id_str}]"
        modified_opening_fence = opening_fence.rstrip('\r\n') + id_tag_display + '\n'
        
        processed_text_parts.append(modified_opening_fence)
        processed_text_parts.append(code_content)
        processed_text_parts.append(closing_fence)
        
        current_global_id += 1
        last_end = end_block
            
    processed_text_parts.append(markdown_text[last_end:])
    return "".join(processed_text_parts), found_blocks, current_global_id

class SessionManager:
    """
    Manages chat sessions, including loading, saving, creating new sessions,
    and handling persistent code block IDs.
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
        Initializes code block fields if loading an older session format.
        Returns True if a session was successfully loaded, False otherwise.
        """
        if session_id is None:
            session_id = self._load_last_session_id()

        if session_id:
            filepath = self.get_session_filepath(session_id)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        loaded_data = json.load(f)
                        self.current_session_data = loaded_data
                        self.current_session_id = session_id

                        # Ensure new fields exist for backward compatibility
                        if "code_blocks" not in self.current_session_data:
                            self.current_session_data["code_blocks"] = {}
                        if "next_code_block_global_id" not in self.current_session_data:
                            # If loading an old session, we might need to re-process history
                            # For simplicity now, just start new IDs. A more robust migration
                            # would re-scan conversation_history.
                            self.current_session_data["next_code_block_global_id"] = 1 
                            # Potentially re-process existing history here if needed for old sessions
                            # self._reprocess_history_for_code_blocks()


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

    # Optional: Method to re-process history of old sessions if they are loaded
    # def _reprocess_history_for_code_blocks(self):
    #     all_new_blocks = {}
    #     next_id = 1
    #     processed_history = []
    #     for msg in self.current_session_data.get("conversation_history", []):
    #         if msg.get("role") == "assistant":
    #             processed_content, new_blocks, next_id_after_msg = _process_text_for_code_blocks(msg["content"], next_id)
    #             msg["content"] = processed_content
    #             all_new_blocks.update(new_blocks)
    #             next_id = next_id_after_msg
    #         processed_history.append(msg)
    #     self.current_session_data["conversation_history"] = processed_history
    #     self.current_session_data["code_blocks"] = all_new_blocks
    #     self.current_session_data["next_code_block_global_id"] = next_id


    def save_session(self):
        """Saves the current session data (including code blocks) to a file."""
        if not self.current_session_id:
            # print("No active session to save.") # Can be noisy
            return

        filepath = self.get_session_filepath(self.current_session_id)
        try:
            self.current_session_data.setdefault("metadata", {})
            self.current_session_data["metadata"]["last_modified"] = datetime.now().isoformat()

            with open(filepath, 'w') as f:
                json.dump(self.current_session_data, f, indent=4)
            self._save_last_session_id()
        except IOError as e:
            print(f"Error saving session {self.current_session_id} to {filepath}: {e}")
        except TypeError as e:
            print(f"Error serializing session data for {self.current_session_id}: {e}")

    def new_session(self, session_id: str | None = None, session_name: str | None = None):
        """
        Starts a new session, optionally with a given ID and name.
        Resets code block tracking.
        """
        # Save the old session first if one was active
        if self.current_session_id:
            self.save_session()

        self.current_session_id = session_id if session_id else str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Reset session data for the new session
        self.current_session_data = {
            "conversation_history": [],
            "metadata": {
                "created_at": timestamp.isoformat(),
                "name": session_name if session_name else f"Chat Session {timestamp.strftime('%Y-%m-%d %H:%M')}"
            },
            "code_blocks": {}, # Reset code blocks
            "next_code_block_global_id": 1 # Reset ID counter
        }
        print(f"Started new session: {self.current_session_data['metadata'].get('name', self.current_session_id)}")
        self.save_session() # Save the newly created empty session

    def add_message_to_history(self, role: str, content: str):
        """
        Adds a message to the history. If it's an assistant message,
        it processes the content for code blocks, assigns global IDs,
        stores them, and embeds ID tags in the content.
        """
        if role == "assistant":
            processed_content, new_blocks, next_id = _process_text_for_code_blocks(
                content,
                self.current_session_data.get("next_code_block_global_id", 1)
            )
            
            self.current_session_data.setdefault("conversation_history", []).append({"role": role, "content": processed_content})
            self.current_session_data.setdefault("code_blocks", {}).update(new_blocks)
            self.current_session_data["next_code_block_global_id"] = next_id
        else: # User messages or system messages (if you add them directly to history)
            self.current_session_data.setdefault("conversation_history", []).append({"role": role, "content": content})
        
        # Auto-save after each message
        self.save_session()

    def get_code_block(self, block_id_str: str) -> str | None:
        """Retrieves code content by its global string ID."""
        return self.current_session_data.get("code_blocks", {}).get(block_id_str)

    def get_conversation_history(self) -> list:
        """Returns the conversation history of the current session."""
        return self.current_session_data.get("conversation_history", [])

    def clear_current_session_history(self):
        """Clears the conversation history, code blocks, and resets code block ID counter for the current session."""
        if self.current_session_id:
            self.current_session_data["conversation_history"] = []
            self.current_session_data["code_blocks"] = {}
            self.current_session_data["next_code_block_global_id"] = 1
            self.save_session()
            print(f"Conversation history cleared for session '{self.current_session_data['metadata'].get('name', self.current_session_id)}'.")
        else:
            print("No active session to clear.")

    def list_sessions(self) -> list:
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
