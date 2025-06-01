'''
Utility functions for text processing, particularly for handling code blocks in markdown.
'''

# This file previously contained _process_text_for_code_blocks.
# That functionality has been moved and enhanced in retrochat_app.core.code_block_utils.py
# under the function `process_and_assign_code_block_ids`.

# The CODE_BLOCK_PATTERN regex from the old _process_text_for_code_blocks
# has also been refined and moved to code_block_utils.py as CODE_BLOCK_RECONSTRUCTION_PATTERN.

# This file now primarily contains other text processing utilities like process_token_stream.


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
                yield {"type": "text", "content": chunk.lstrip(" \t\r\n")}
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
                        yield {"type": "text", "content": stash.lstrip(" \t\r\n")}
                        out_started = True
                    elif out_started:
                        yield {"type": "text", "content": stash}
                    stash = ""
                else:
                    if start:
                        text_before_think = stash[:start]
                        if not out_started and text_before_think.strip():
                            yield {"type": "text", "content": text_before_think.lstrip(" \t\r\n")}
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
