#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.core.text_processing_utils import _process_text_for_code_blocks

# What if the LLM provided this malformed content?
malformed_llm_content = """Sure! Here's a simple Python program that asks the user for their name and then greets them:

```python# A simple Python program to greet the user

name = input("Enter your name: ")
print(f"Hello, {name}! Welcome to Python.")```

### What this code does:
- `input("Enter your name: ")` prompts the user to enter their name."""

print("=== TESTING MALFORMED LLM INPUT ===")
print("Input from LLM:")
print(repr(malformed_llm_content))

print("\n=== PROCESSING ===")
processed_content, found_blocks, next_id = _process_text_for_code_blocks(malformed_llm_content, 1)

print("After processing:")
print(repr(processed_content))
print(f"\nFound blocks: {len(found_blocks)}")

if found_blocks:
    print("Blocks found:")
    for block_id, content in found_blocks.items():
        print(f"  {block_id}: {repr(content)}")
else:
    print("No blocks found - this explains the malformed session content!")
    
print("\n=== THE ISSUE ===")
print("If the LLM provides malformed markdown, it won't be processed")
print("and will be stored as-is in the session. Later, when loaded,")
print("the CodeBlockFormatter can't parse it either, leading to display issues.")
