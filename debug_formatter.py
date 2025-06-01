#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.ui.code_block_formatter import CodeBlockFormatter

# Test session data
session_data = {
    "code_blocks": {
        "1": "# A simple Python program to greet the user\n\nname = input(\"Enter your name: \")\nprint(f\"Hello, {name}! Welcome to Python.\")"
    },
    "next_code_block_global_id": 2
}

# Content from the session file that's causing issues
test_content = """Sure! Here's a simple Python program that asks the user for their name and then greets them:

```python [CodeID: 1]
# A simple Python program to greet the user

name = input("Enter your name: ")
print(f"Hello, {name}! Welcome to Python.")
```

### What this code does:
- `input("Enter your name: ")` prompts the user to enter their name."""

formatter = CodeBlockFormatter(session_data)

print("=== TESTING CODE BLOCK FORMATTER ===")
print("Input content:")
print(repr(test_content))
print("\nInput content (display):")
print(test_content)

print("\n=== FORMAT FOR DISPLAY ===")
renderables = formatter.format_for_display(test_content)

print(f"Number of renderables: {len(renderables)}")
for i, renderable in enumerate(renderables):
    print(f"\nRenderable {i}: {type(renderable)}")
    if hasattr(renderable, 'plain'):
        print(f"Content: {repr(renderable.plain)}")
    elif hasattr(renderable, 'renderable'):
        print(f"Panel content type: {type(renderable.renderable)}")
    else:
        print(f"Content: {repr(str(renderable))}")
