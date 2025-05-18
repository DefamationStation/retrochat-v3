import re
import logging # Added
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.markdown import Markdown # Added for consistency, though not directly used in this snippet

from retrochat_app.core.code_block_utils import CODE_BLOCK_PATTERN # Import the robust regex

class CodeBlockFormatter:
    """
    Manages the creation, storage, and display formatting of code blocks
    within assistant messages, using a direct reference to session data.
    """
    # Use the more robust regex from code_block_utils.py
    REGEX_CODE_BLOCK = CODE_BLOCK_PATTERN

    def __init__(self, session_data: dict):
        """
        Initializes the formatter with a reference to the session's data dictionary.
        Ensures 'code_blocks' and 'next_code_block_global_id' are initialized if not present.
        """
        self.logger = logging.getLogger(__name__) # Added
        self.session_data = session_data
        if "code_blocks" not in self.session_data:
            self.session_data["code_blocks"] = {}
            self.logger.debug(f"Initialized 'code_blocks' in session_data.") # Added
        if "next_code_block_global_id" not in self.session_data:
            self.session_data["next_code_block_global_id"] = 1
            self.logger.debug(f"Initialized 'next_code_block_global_id' to 1 in session_data.") # Added
        self.logger.debug(f"CodeBlockFormatter initialized. Current IDs: {list(self.session_data['code_blocks'].keys())}, Next ID: {self.session_data['next_code_block_global_id']}") # Added

    # Removed load_from_session method

    def reset(self):
        """Resets the code block information in the session data."""
        self.logger.debug("Resetting CodeBlockFormatter state in session_data.") # Added
        self.session_data["code_blocks"] = {}
        self.session_data["next_code_block_global_id"] = 1

    def _store_and_get_id(self, code_content: str) -> str:
        """
        Stores the code block content in session_data if new, or returns existing ID.
        """
        self.logger.debug(f"Attempting to store/get ID for code content (first 50 chars): {code_content[:50].strip()}...") # Added
        # Check if this exact code content already exists
        for existing_id, existing_content in self.session_data["code_blocks"].items():
            if existing_content == code_content:
                self.logger.debug(f"Found existing ID '{existing_id}' for content.") # Added
                return existing_id
        
        # If not, store it with a new ID
        new_id = str(self.session_data["next_code_block_global_id"])
        self.session_data["code_blocks"][new_id] = code_content
        self.session_data["next_code_block_global_id"] += 1
        self.logger.debug(f"Stored new code block with ID '{new_id}'. Next ID is now {self.session_data['next_code_block_global_id']}.") # Added
        return new_id

    def get_code_by_id(self, block_id: str) -> str | None:
        """Retrieves code content by its global ID from session_data."""
        code = self.session_data["code_blocks"].get(block_id)
        if code:
            self.logger.debug(f"Retrieved code for ID '{block_id}'.") # Added
        else:
            self.logger.warning(f"Failed to retrieve code for ID '{block_id}'. Available IDs: {list(self.session_data['code_blocks'].keys())}") # Added
        return code

    def format_for_display(self, text: str) -> list:
        """
        Formats text containing code blocks for display.
        Extracts code blocks, stores them, assigns IDs, and prepares renderables.
        """
        self.logger.debug(f"Formatting text for display (length: {len(text)}). Input text (first 100 chars): {text[:100].encode('utf-8', 'replace').decode('utf-8')}")
        renderables = []
        last_end = 0

        # Now uses the robust REGEX_CODE_BLOCK from code_block_utils
        # The REGEX_CODE_BLOCK is already compiled with re.DOTALL, so no need to pass flags here.
        for match in re.finditer(self.REGEX_CODE_BLOCK, text):
            self.logger.debug(f"Regex found a code block match: {match.group(0)[:70].encode('utf-8', 'replace').decode('utf-8')}...")
            start, end = match.span()
            
            # Add preceding text if any
            if start > last_end:
                preceding_text = text[last_end:start].strip()
                if preceding_text:
                    # Using Markdown for non-code text parts
                    renderables.append(Markdown(preceding_text))

            # Extract parts using the new regex groups
            language = match.group(1).strip() if match.group(1) else "plaintext" # Group 1: Language
            existing_code_id = match.group(2)  # Group 2: Existing CodeID (string or None)
            code_content = match.group(3).strip()    # Group 3: Clean code content
            
            self.logger.debug(f"Parsed - Lang: '{language}', ExistingID: '{existing_code_id}', Code (start): '{code_content[:30]}...'")

            block_id_to_use: str
            if existing_code_id:
                # An ID was present in the markdown. Use it.
                block_id_to_use = existing_code_id
                self.logger.info(f"Using existing CodeID '{block_id_to_use}' from parsed markdown for content (first 30): {code_content[:30]}...")
                
                # CRUCIAL FIX: Store/update the code content for this ID.
                # This ensures that if the markdown contains an ID (from history or LLM),
                # the formatter's understanding of that ID's content is up-to-date with the
                # (stripped) version of the code it just parsed from the input text.
                self.session_data["code_blocks"][block_id_to_use] = code_content 
                self.logger.debug(f"Stored/Updated code for ID '{block_id_to_use}' in session_data. Content (first 30): {code_content[:30]}...")

                # Ensure next_code_block_global_id is at least past this ID
                current_next_id = self.session_data.get("next_code_block_global_id", 1)
                if int(block_id_to_use) >= current_next_id:
                    self.session_data["next_code_block_global_id"] = int(block_id_to_use) + 1
                    self.logger.debug(f"Updated next_code_block_global_id to {self.session_data['next_code_block_global_id']} due to existing_code_id {block_id_to_use}")
            else:
                # No CodeID in markdown (e.g., new block in current session, or old format without tags).
                # Store it (if new) and get/generate an ID using the clean code_content.
                self.logger.info(f"No existing CodeID found in markdown. Calling _store_and_get_id for content: {code_content[:30]}...")
                block_id_to_use = self._store_and_get_id(code_content) # This handles storing and ID generation
            
            panel = Panel(
                Syntax(code_content, language, theme="dracula", line_numbers=True, word_wrap=True),
                title=f"Language: {language}", # Title shows clean language
                border_style="blue",
                expand=False
            )
            renderables.append(panel)
            # Display the CodeID (either existing or newly generated)
            renderables.append(Text(f"CodeID {block_id_to_use}", style="dim"))
            
            last_end = end

        # Add remaining text if any
        if last_end < len(text):
            remaining_text = text[last_end:].strip()
            if remaining_text:
                renderables.append(Markdown(remaining_text)) # Use Markdown for regular text
        
        # If no code blocks were found at all, and original text was not just whitespace
        if not renderables and text.strip():
            renderables.append(Markdown(text.strip()))
        elif not text.strip() and not renderables: # Handle empty or whitespace-only input if nothing else rendered
             renderables.append(Text(""))

        return renderables
