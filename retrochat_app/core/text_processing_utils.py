'''
Utility functions for text processing, particularly for handling code blocks in markdown.
'''
import re

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
        opening_fence = match.group(1) # e.g., ```python\\n or ```python  \\r\\n
        code_content = match.group(2)  # The actual code
        closing_fence = match.group(3) # e.g., \\n```

        # Extract the actual newline character(s) from the end of the opening_fence
        newline_char_match = re.search(r"(\r\n|\n|\r)$", opening_fence)
        # Fallback to \\n if regex somehow didn't ensure newline_char_match (should not happen with current regex)
        newline_char = newline_char_match.group(0) if newline_char_match else '\\n'
        
        # Get the content of the opening fence line, without the trailing newline
        content_of_opening_fence_line = opening_fence[:-len(newline_char)]

        block_id_str = str(current_global_id)
        found_blocks[block_id_str] = code_content
        
        # Add text before this code block
        processed_text_parts.append(markdown_text[last_end:start_block])
        
        # Create the ID tag to be inserted, with a leading space
        id_tag_display = f" [CodeID: {block_id_str}]"
        
        # Insert the ID tag: strip trailing spaces from fence content, add tag, then add original newline
        modified_opening_fence = content_of_opening_fence_line.rstrip() + id_tag_display + newline_char
        
        processed_text_parts.append(modified_opening_fence)
        processed_text_parts.append(code_content)
        processed_text_parts.append(closing_fence)
        
        current_global_id += 1
        last_end = end_block
            
    processed_text_parts.append(markdown_text[last_end:])
    return "".join(processed_text_parts), found_blocks, current_global_id
