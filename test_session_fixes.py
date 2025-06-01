#!/usr/bin/env python3
"""
Test script to verify fixes work with the exact content from session files.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.core.text_processing_utils import _process_text_for_code_blocks
from retrochat_app.core.code_block_utils import CODE_BLOCK_PATTERN
import re

def test_session_content():
    """Test with actual content from session files."""
    
    # Exact content from the session file (malformed)
    session_content = '''Sure! Here's a simple Python program that asks the user for their name and then greets them:

```python [CodeID: 1]# A simple Python program to greet the user

name = input("Enter your name: ")
print(f"Hello, {name}! Welcome to Python.")```

### What this code does:
- `input("Enter your name: ")` prompts the user to enter their name.'''
    
    print("Testing session-like content with existing CodeID...")
    print("=" * 60)
    print(f"INPUT:\n{repr(session_content)}")
    
    # Process the content
    processed_text, found_blocks, next_id = _process_text_for_code_blocks(session_content, 10)
    
    print(f"\nPROCESSED:\n{repr(processed_text)}")
    print(f"\nFOUND BLOCKS ({len(found_blocks)}):")
    for block_id, content in found_blocks.items():
        print(f"  Block {block_id}: {repr(content[:50])}...")
    print(f"NEXT ID: {next_id}")
    
    # Test regex extraction
    matches = list(CODE_BLOCK_PATTERN.finditer(processed_text))
    print(f"\nREGEX MATCHES: {len(matches)}")
    for i, match in enumerate(matches):
        lang = match.group(1) or '(no lang)'
        code_id = match.group(2) or '(no id)'
        content = match.group(3)[:50] + '...' if len(match.group(3)) > 50 else match.group(3)
        print(f"  Match {i+1}: lang='{lang}', code_id='{code_id}', content='{content}'")
      # Check if it's properly formatted now
    print(f"\nFORMATTING CHECK:")
    if "```python [CodeID: 1]\n#" in processed_text:
        print("✅ Proper newline after CodeID tag")
    else:
        print("❌ Missing newline after CodeID tag")
    
    if "\n```" in processed_text:
        print("✅ Proper newline before closing fence")
    else:
        print("❌ Missing newline before closing fence")

def test_mixed_content():
    """Test content with both existing and new code blocks."""
    
    mixed_content = '''Here's existing code:

```python [CodeID: 5]print("existing")```

And here's new code:

```python
print("new code")
```'''
    
    print("\n" + "=" * 60)
    print("Testing mixed content (existing + new CodeIDs)...")
    print("=" * 60)
    print(f"INPUT:\n{repr(mixed_content)}")
    
    processed_text, found_blocks, next_id = _process_text_for_code_blocks(mixed_content, 10)
    
    print(f"\nPROCESSED:\n{repr(processed_text)}")
    print(f"\nFOUND BLOCKS ({len(found_blocks)}):")
    for block_id, content in found_blocks.items():
        print(f"  Block {block_id}: {repr(content)}")
    print(f"NEXT ID: {next_id}")

if __name__ == "__main__":
    test_session_content()
    test_mixed_content()
