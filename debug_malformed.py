#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.ui.code_block_formatter import CodeBlockFormatter

# Test content exactly as stored in session - notice there's no newline after [CodeID: 1]
test_content_from_session = """Sure! Here's a simple Python program that asks the user for their name and then greets them:

```python [CodeID: 1]# A simple Python program to greet the user

name = input("Enter your name: ")
print(f"Hello, {name}! Welcome to Python.")```

### What this code does:
- `input("Enter your name: ")` prompts the user to enter their name."""

session_data = {
    "code_blocks": {
        "1": "# A simple Python program to greet the user\n\nname = input(\"Enter your name: \")\nprint(f\"Hello, {name}! Welcome to Python.\")"
    },
    "next_code_block_global_id": 2
}

formatter = CodeBlockFormatter(session_data)

print("=== MALFORMED CONTENT FROM SESSION ===")
print("Input content:")
print(repr(test_content_from_session))
print("\nInput content (display):")
print(test_content_from_session)

print("\n=== FORMAT FOR DISPLAY ===")
renderables = formatter.format_for_display(test_content_from_session)

print(f"Number of renderables: {len(renderables)}")
for i, renderable in enumerate(renderables):
    print(f"\nRenderable {i}: {type(renderable)}")

print("\n=== TESTING REGEX PATTERN ===")
import re
from retrochat_app.core.code_block_utils import CODE_BLOCK_PATTERN

matches = list(CODE_BLOCK_PATTERN.finditer(test_content_from_session))
print(f"Number of matches found: {len(matches)}")
for i, match in enumerate(matches):
    print(f"Match {i}:")
    print(f"  Full match: {repr(match.group(0))}")
    print(f"  Language: {repr(match.group(1))}")
    print(f"  CodeID: {repr(match.group(2))}")
    print(f"  Content: {repr(match.group(3))}")
