"""
Shared utilities for code block regex and extraction logic.
"""
import re

# Renamed original pattern for clarity, used by formatter for parsing display.
# Group 1: language, Group 2: CodeID (optional), Group 3: code_content (may include trailing newline)
CODE_BLOCK_EXTRACTION_PATTERN = re.compile(
    r"```\s*([a-zA-Z0-9_\-\.]*)"        # Optional whitespace then language
    r"(?:\s*\[CodeID:\s*(\d+)\s*\])?"  # Optional CodeID tag
    r"\s*\n?"                            # Optional spaces and newline
    r"(.*?)"                              # Code content
    r"```",                               # Closing fence
    re.DOTALL
)

# New pattern for robust reconstruction, used by the centralized processing function.
CODE_BLOCK_RECONSTRUCTION_PATTERN = re.compile(
    r"(```\s*(?:[a-zA-Z0-9_\.\-]*)\s*)"  # Group 1: Opening fence and language
    r"(?:\s*\[CodeID:\s*(\d+)\s*\])?"      # Group 2: Optional existing CodeID (value only)
    r"(\s*?\n)?"                        # Group 3: Optional newline immediately after fence/CodeID
    r"(.*?)"                            # Group 4: Code content (non-greedy)
    r"(\n?\s*```)",                     # Group 5: Closing fence
    re.DOTALL
)


def process_and_assign_code_block_ids(markdown_text: str, session_data: dict) -> tuple[str, dict[str, str]]:
    """
    Finds code blocks, assigns unique string IDs if not present, stores them in session_data,
    and embeds ID tags in the markdown text. Updates session_data directly.

    Args:
        markdown_text: The input markdown text.
        session_data: The session data dictionary, which contains:
                      - "code_blocks": dict to store {block_id_str: code_content}
                      - "next_code_block_global_id": int, the next available global ID.

    Returns:
        - processed_markdown: Markdown text with ID tags embedded.
        - new_or_updated_blocks: Dictionary of {block_id_str: code_content} for blocks
                                 that were newly assigned an ID or had their content updated
                                 based on an existing ID in the markdown.
    """
    new_or_updated_blocks = {}
    current_global_id = session_data.get("next_code_block_global_id", 1)
    
    if "code_blocks" not in session_data:
        session_data["code_blocks"] = {}

    processed_text_parts = []
    last_end = 0

    for match in CODE_BLOCK_RECONSTRUCTION_PATTERN.finditer(markdown_text):
        start_block, end_block = match.span()
        
        opening_fence_and_lang = match.group(1) 
        existing_code_id_str = match.group(2)   
        # group 3 is newline_after_header, captured for accurate reconstruction
        raw_code_content = match.group(4)       
        closing_fence = match.group(5)          

        processed_text_parts.append(markdown_text[last_end:start_block])

        # Store the stripped version of code content for comparison and storage
        # but use raw_code_content for reconstruction to preserve original internal formatting.
        stored_code_content = raw_code_content.strip() 
        block_id_to_use_str: str

        if existing_code_id_str:
            block_id_to_use_str = existing_code_id_str
            # Update the stored content for this ID with the potentially newer version from markdown
            session_data["code_blocks"][block_id_to_use_str] = stored_code_content
            new_or_updated_blocks[block_id_to_use_str] = stored_code_content
            # Ensure next_code_block_global_id is ahead
            if int(block_id_to_use_str) >= current_global_id:
                current_global_id = int(block_id_to_use_str) + 1
        else:
            # No ID in markdown, try to find by content or assign new
            found_existing_id_for_content = None
            for id_val, content_val in session_data.get("code_blocks", {}).items():
                if content_val == stored_code_content: # Compare with stripped content
                    found_existing_id_for_content = id_val
                    break
            
            if found_existing_id_for_content:
                block_id_to_use_str = found_existing_id_for_content
                # Ensure content is updated if somehow it changed for an existing ID found by content match
                session_data["code_blocks"][block_id_to_use_str] = stored_code_content
                new_or_updated_blocks[block_id_to_use_str] = stored_code_content
            else:
                block_id_to_use_str = str(current_global_id)
                session_data["code_blocks"][block_id_to_use_str] = stored_code_content
                new_or_updated_blocks[block_id_to_use_str] = stored_code_content
                current_global_id += 1
        
        # Reconstruct the block with the CodeID tag
        # Ensure the opening fence (e.g., ```python) is clean, then add the tag
        formatted_opening_fence = opening_fence_and_lang.rstrip() + f" [CodeID: {block_id_to_use_str}]"
        
        # Ensure newline after header, then raw content, then closing fence
        # The raw_code_content preserves internal newlines.
        # The closing_fence (group 5) includes its preceding newline if it was there.
        # If not, add one.
        final_closing_fence = closing_fence
        if not closing_fence.startswith('\n') and closing_fence == '```': # handles ``` closing on same line as code
            final_closing_fence = '\n```'
        elif not closing_fence.startswith('\n'): # handles ``` closing on next line but without explicit \n in group
             final_closing_fence = '\n' + closing_fence.lstrip()


        reconstructed_block = f"{formatted_opening_fence}\n{raw_code_content}{final_closing_fence}"
        
        processed_text_parts.append(reconstructed_block)
        last_end = end_block

    processed_text_parts.append(markdown_text[last_end:])
    session_data["next_code_block_global_id"] = current_global_id
    
    return "".join(processed_text_parts), new_or_updated_blocks


def extract_code_blocks(markdown_text): # Existing function, ensure it uses the renamed pattern if it's for the formatter
    """
    Finds all code blocks in markdown_text using CODE_BLOCK_EXTRACTION_PATTERN.
    Returns a list of tuples: (language, code_id, code_content, match_span)
    code_id may be None if not present.
    """
    results = []
    # Ensure this uses the correct pattern, assuming CODE_BLOCK_EXTRACTION_PATTERN is for this.
    for match in CODE_BLOCK_EXTRACTION_PATTERN.finditer(markdown_text):
        language = match.group(1).strip() if match.group(1) else "text" # Ensure language is stripped
        code_id = match.group(2) # This is already just the number string or None
        # The content from EXTRACTION_PATTERN (group 3) is what's between the fences (after optional ID and newline)
        # and before the closing ```. It should be stripped for consistent storage and comparison.
        code_content = match.group(3).strip() 
        results.append((language, code_id, code_content, match.span()))
    return results
