#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.core.text_processing_utils import _process_text_for_code_blocks
from retrochat_app.ui.code_block_formatter import CodeBlockFormatter

# Original content that LLM would provide
original_llm_content = """Sure! Here's a simple Python program that asks the user for their name and then greets them:

```python
# A simple Python program to greet the user

name = input("Enter your name: ")
print(f"Hello, {name}! Welcome to Python.")
```

### What this code does:
- `input("Enter your name: ")` prompts the user to enter their name."""

print("=== STEP 1: LLM PROVIDES CONTENT ===")
print(repr(original_llm_content))

print("\n=== STEP 2: PROCESS FOR STORAGE ===")
processed_content, found_blocks, next_id = _process_text_for_code_blocks(original_llm_content, 1)
print("Processed content:")
print(repr(processed_content))
print("\nFound blocks:")
for block_id, block_content in found_blocks.items():
    print(f"  {block_id}: {repr(block_content)}")

print("\n=== STEP 3: SIMULATE STORAGE & RELOAD ===")
# This is what would be stored in session_data
session_data = {
    "code_blocks": found_blocks,
    "next_code_block_global_id": next_id
}

print("Session data created:")
print(f"  code_blocks: {session_data['code_blocks']}")
print(f"  next_id: {session_data['next_code_block_global_id']}")

print("\n=== STEP 4: LOAD FROM SESSION AND FORMAT FOR DISPLAY ===")
formatter = CodeBlockFormatter(session_data)
renderables = formatter.format_for_display(processed_content)

print(f"Number of renderables: {len(renderables)}")

print("\n=== STEP 5: SIMULATE WHAT HAPPENS ON DISPLAY ===")
# This simulates what _display_loaded_history does
print("Processed content as it would be displayed:")
print(processed_content)
