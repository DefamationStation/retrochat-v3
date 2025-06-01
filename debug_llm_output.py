#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.core.text_processing_utils import _process_text_for_code_blocks

# Test what might have been the original LLM output that caused the issue
# Maybe the LLM provided malformed markdown?

test_cases = [
    # Case 1: Proper markdown
    """Here's a simple example:

```python
# A simple program
print("Hello")
```

That's it!""",
    
    # Case 2: Malformed - no newline after language
    """Here's a simple example:

```python# A simple program
print("Hello")
```

That's it!""",
    
    # Case 3: Malformed - no newline before closing
    """Here's a simple example:

```python
# A simple program
print("Hello")```

That's it!""",
    
    # Case 4: Both malformed
    """Here's a simple example:

```python# A simple program
print("Hello")```

That's it!"""
]

for i, test_content in enumerate(test_cases):
    print(f"\n=== TEST CASE {i+1} ===")
    print("Input:")
    print(repr(test_content))
    
    try:
        processed_content, found_blocks, next_id = _process_text_for_code_blocks(test_content, 1)
        print("\nProcessed:")
        print(repr(processed_content))
        print(f"\nFound blocks: {len(found_blocks)}")
        if found_blocks:
            for block_id, block_content in found_blocks.items():
                print(f"  Block {block_id}: {repr(block_content)}")
    except Exception as e:
        print(f"\nError: {e}")
    
    print("-" * 50)
