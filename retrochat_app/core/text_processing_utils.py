'''
Utility functions for text processing, particularly for handling code blocks in markdown.
'''
import re

def _process_text_for_code_blocks(markdown_text: str, starting_id: int) -> tuple[str, dict[str, str], int]:
    """
    Finds code blocks, assigns unique string IDs, stores them, and embeds ID tags in the text.
    The ID tag is placed on the same line as the opening fence.
    
    Handles both well-formed and malformed code blocks:
    - Well-formed: ```python\ncode\n```
    - Malformed: ```python [CodeID: X]code``` (missing newlines)
    
    Returns:
        - processed_markdown: Markdown text with ID tags embedded.
        - found_blocks: Dictionary of {block_id_str: code_content} for newly found blocks.
        - next_id: The next available global ID.
    """
    found_blocks = {}
    current_global_id = starting_id
    
    # More robust regex that captures opening fence and checks for existing CodeID
    # Captures: group(1)=fence_with_lang, group(2)=optional_existing_codeid, 
    #          group(3)=optional_newline, group(4)=code_content, group(5)=closing
    code_block_pattern = re.compile(
        r"(```\s*(?:[a-zA-Z0-9_\-]*)\s*)(?:\[CodeID: (\d+)\]\s*)?(\n?)(.*?)(\n?```)", 
        re.MULTILINE | re.DOTALL
    )
    
    processed_text_parts = []
    last_end = 0
    
    for match in code_block_pattern.finditer(markdown_text):
        start_block, end_block = match.span()
        fence_with_lang = match.group(1)        # e.g., "```python " 
        existing_code_id = match.group(2)       # Existing CodeID if present
        newline_after_fence = match.group(3)    # Optional newline after fence/CodeID
        code_content = match.group(4)           # The actual code content
        closing_part = match.group(5)           # Optional newline + ```

        # Determine the block ID to use
        if existing_code_id:
            # Use existing CodeID, don't increment counter
            block_id_str = existing_code_id
        else:
            # Create new CodeID
            block_id_str = str(current_global_id)
            current_global_id += 1
        
        found_blocks[block_id_str] = code_content
        
        # Add text before this code block
        processed_text_parts.append(markdown_text[last_end:start_block])
        
        # Reconstruct with proper formatting
        opening_fence_clean = fence_with_lang.rstrip()
        id_tag_display = f" [CodeID: {block_id_str}]"
        
        # Always ensure proper newline after the CodeID tag
        if newline_after_fence:
            opening_fence_final = opening_fence_clean + id_tag_display + newline_after_fence
        else:
            # Add missing newline for malformed blocks
            opening_fence_final = opening_fence_clean + id_tag_display + '\n'
          # Ensure proper closing
        if closing_part.startswith('\n'):
            closing_final = closing_part
        elif closing_part == '```':
            # Missing newline before closing fence
            closing_final = '\n```'
        else:
            # Some other format, try to fix it
            closing_final = '\n' + closing_part
        
        processed_text_parts.append(opening_fence_final)
        processed_text_parts.append(code_content)
        processed_text_parts.append(closing_final)
        
        last_end = end_block
    
    processed_text_parts.append(markdown_text[last_end:])
    return "".join(processed_text_parts), found_blocks, current_global_id


def process_token_stream(token_iterable, include_thoughts=False):
    """
    Processes a raw token stream, handling <think> tags and yielding display-ready chunks.

    Args:
        token_iterable: An iterable of tokens, where tokens can be strings or dicts.
        include_thoughts (bool): Whether to include thoughts in the output.

    Yields:
        dict: Processed chunks, e.g., {"type": "text", "content": "hello"}
              or {"type": "thought", "content": "thinking..."}.
    """
    tag_open, tag_close = "<think>", "</think>"
    in_think = False
    stash = ""
    out_started = False  # have we yielded a visible char yet?

    for chunk in token_iterable:
        # out-of-band “thought” packets
        if isinstance(chunk, dict) and chunk.get("type") == "thought":
            if include_thoughts:
                yield {"type": "thought", "content": chunk["content"]}
            continue

        if not isinstance(chunk, str):
            continue

        if include_thoughts:
            if not out_started and chunk.strip():
                yield {"type": "text", "content": chunk.lstrip(" \\t\\r\\n")}
                out_started = True
            elif out_started:
                yield {"type": "text", "content": chunk}
            continue

        # strip inline <think>…</think>
        stash += chunk
        while stash:
            if not in_think:
                start = stash.find(tag_open)
                if start == -1:
                    if not out_started and stash.strip():
                        yield {"type": "text", "content": stash.lstrip(" \\t\\r\\n")}
                        out_started = True
                    elif out_started:
                        yield {"type": "text", "content": stash}
                    stash = ""
                else:
                    if start:
                        text_before_think = stash[:start]
                        if not out_started and text_before_think.strip():
                            yield {"type": "text", "content": text_before_think.lstrip(" \\t\\r\\n")}
                            out_started = True
                        elif out_started:
                            yield {"type": "text", "content": text_before_think}
                    stash = stash[start + len(tag_open):]
                    in_think = True
            else:  # in_think
                end = stash.find(tag_close)
                if end == -1:
                    # still inside think: drop everything so far by not yielding
                    stash = ""
                else:
                    # We were in a think block, and it just closed.
                    # The content within the think block is implicitly dropped.
                    stash = stash[end + len(tag_close):]
                    in_think = False
