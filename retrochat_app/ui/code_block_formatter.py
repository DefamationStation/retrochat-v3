import re
import logging # Added
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.markdown import Markdown # Added for consistency, though not directly used in this snippet

# Use the EXTRACTION pattern for display parsing, not the reconstruction one.
from retrochat_app.core.code_block_utils import CODE_BLOCK_EXTRACTION_PATTERN, extract_code_blocks 

class CodeBlockFormatter:
    """
    Manages the display formatting of code blocks within assistant messages.
    It uses `extract_code_blocks` to find blocks and their IDs (if present in the text)
    and then retrieves the definitive code content from `session_data` using these IDs.
    It no longer assigns or stores code blocks itself.
    """
    # Use the extraction-focused regex from code_block_utils.py
    REGEX_CODE_BLOCK = CODE_BLOCK_EXTRACTION_PATTERN

    def __init__(self, session_data: dict):
        """
        Initializes the formatter with a reference to the session's data dictionary.
        """
        self.logger = logging.getLogger(__name__) 
        self.session_data = session_data
        # No longer initializes code_blocks or next_code_block_global_id here,
        # as this class is now only for formatting/display based on existing session_data.
        self.logger.debug(f"CodeBlockFormatter initialized. Accessing session_data for code blocks.")

    # Removed reset method, as state is managed by SessionManager.
    # Removed _store_and_get_id method, as storage and ID generation is centralized.

    def get_code_by_id(self, block_id: str) -> str | None:
        """Retrieves code content by its global ID from session_data."""
        code = self.session_data.get("code_blocks", {}).get(block_id)
        if code:
            self.logger.debug(f"Retrieved code for ID '{block_id}'.")
        else:
            self.logger.warning(f"Failed to retrieve code for ID '{block_id}'. Available IDs in session: {list(self.session_data.get('code_blocks', {}).keys())}")
        return code

    def format_for_display(self, text: str) -> list:
        """
        Formats text containing code blocks for display.
        Uses `extract_code_blocks` to find block details (lang, ID, raw content from text).
        If an ID is found, it prioritizes fetching content from `session_data` using that ID.
        """
        self.logger.debug(f"Formatting text for display (length: {len(text)}). Input text (first 100 chars): {text[:100].encode('utf-8', 'replace').decode('utf-8')}")
        renderables = []
        last_end = 0

        # Use the centralized extract_code_blocks function
        # It returns (language, code_id_from_text, raw_code_content_from_text, match_span)
        extracted_blocks = extract_code_blocks(text)

        for lang_from_text, id_from_text, raw_content_from_text, (start, end) in extracted_blocks:
            self.logger.debug(f"Processing extracted block: Lang='{lang_from_text}', ID='{id_from_text}', Span=({start},{end}), RawContent (start): '{raw_content_from_text[:30].strip()}...'")
            
            # Add preceding text if any
            if start > last_end:
                preceding_text = text[last_end:start].strip()
                if preceding_text:
                    renderables.append(Markdown(preceding_text))

            code_to_display: str | None = None
            block_id_to_show: str | None = id_from_text
            language_to_use = lang_from_text if lang_from_text else "text"

            if id_from_text:
                # An ID was present in the markdown. Fetch content from session_data.
                code_from_session = self.get_code_by_id(id_from_text)
                if code_from_session is not None:
                    code_to_display = code_from_session
                    self.logger.info(f"Using content from session_data for CodeID '{id_from_text}'.")
                else:
                    # ID in text, but not in session_data. This is an issue.
                    # Fallback to raw content from text for display, but log a warning.
                    code_to_display = raw_content_from_text.strip() # Use stripped raw content as fallback
                    self.logger.warning(f"CodeID '{id_from_text}' found in text but not in session_data. Displaying raw content from text.")
            else:
                # No CodeID in markdown. This implies the text hasn't been processed by
                # session_manager to embed IDs yet, or it's a very old format.
                # For display, we have to use the raw content. This scenario should be rare
                # if messages are always processed by SessionManager first.
                code_to_display = raw_content_from_text.strip() # Use stripped raw content
                self.logger.warning(f"No CodeID found in markdown for block starting with '{raw_content_from_text[:30].strip()}...'. Displaying raw content. This might indicate unprocessed text.")
                # We don't have an authoritative ID to show in this case.
                block_id_to_show = None 

            if code_to_display is not None:
                panel = Panel(
                    Syntax(code_to_display, language_to_use, theme="dracula", line_numbers=True, word_wrap=True),
                    title=f"Language: {language_to_use}",
                    border_style="blue",
                    expand=False
                )
                renderables.append(panel)
                if block_id_to_show:
                    renderables.append(Text(f"CodeID {block_id_to_show}", style="dim"))
                else:
                    renderables.append(Text("CodeID: N/A (not found in session)", style="dim warning"))
            
            last_end = end

        # Add remaining text if any
        if last_end < len(text):
            remaining_text = text[last_end:].strip()
            if remaining_text:
                renderables.append(Markdown(remaining_text))
        
        if not renderables and text.strip():
            renderables.append(Markdown(text.strip()))
        elif not text.strip() and not renderables: 
             renderables.append(Text(""))

        return renderables
