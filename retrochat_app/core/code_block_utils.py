"""
Shared utilities for code block regex and extraction logic.
"""
import re

# Unified regex pattern for fenced code blocks (with optional language and optional [CodeID: N] tag)
# Updated to handle malformed markdown where newlines might be missing
CODE_BLOCK_PATTERN = re.compile(
    r"```([a-zA-Z0-9_\-\.]*)(?:\s*\[CodeID: (\d+)\])?\s*\n?(.*?)```",
    re.DOTALL
)

def extract_code_blocks(markdown_text):
    """
    Finds all code blocks in markdown_text.
    Returns a list of tuples: (language, code_id, code_content, match_span)
    code_id may be None if not present.
    """
    results = []
    for match in CODE_BLOCK_PATTERN.finditer(markdown_text):
        language = match.group(1) or "text"
        code_id = match.group(2)
        code_content = match.group(3)
        results.append((language, code_id, code_content, match.span()))
    return results
