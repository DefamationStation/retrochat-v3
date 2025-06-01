#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.core.text_processing_utils import _process_text_for_code_blocks

# Test the original content that should be processed
test_content = """Sure! Here's a simple Python program that asks the user for their name and then greets them:

```python
# A simple Python program to greet the user

name = input("Enter your name: ")
print(f"Hello, {name}! Welcome to Python.")
```

### What this code does:
- `input("Enter your name: ")` prompts the user to enter their name.
- The entered name is stored in the variable `name`.
- `print(f"Hello, {name}! Welcome to Python.")` displays a greeting using an f-string (formatted string literal).

Would you like an example of something more specific, like working with lists, loops, or functions? 😊"""

print("=== ORIGINAL CONTENT ===")
print(repr(test_content))
print("\n=== ORIGINAL CONTENT (display) ===")
print(test_content)

print("\n=== PROCESSING ===")
processed_content, found_blocks, next_id = _process_text_for_code_blocks(test_content, 1)

print("\n=== PROCESSED CONTENT ===")
print(repr(processed_content))
print("\n=== PROCESSED CONTENT (display) ===")
print(processed_content)

print(f"\n=== FOUND BLOCKS ===")
for block_id, block_content in found_blocks.items():
    print(f"Block {block_id}:")
    print(repr(block_content))
    print("---")

print(f"\n=== NEXT ID: {next_id} ===")
