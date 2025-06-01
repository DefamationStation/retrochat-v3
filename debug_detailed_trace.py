#!/usr/bin/env python3

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Let me manually trace through the _process_text_for_code_blocks logic

original_content = """Sure! Here's a simple Python program:

```python
# A simple program
print("Hello")
```

That's it!"""

print("=== DETAILED TRACE ===")
print("Original content:")
print(repr(original_content))

# The regex pattern from the function
code_block_pattern = re.compile(
    r"^(```\s*(?:[a-zA-Z0-9_\\-]*)\s*(?:\r\n|\n|\r))(.*?)((?:\r\n|\n|\r)```\s*)$", 
    re.MULTILINE | re.DOTALL
)

matches = list(code_block_pattern.finditer(original_content))
print(f"\nFound {len(matches)} matches")

for i, match in enumerate(matches):
    print(f"\nMatch {i}:")
    opening_fence = match.group(1)
    code_content = match.group(2)
    closing_fence = match.group(3)
    
    print(f"  Opening fence: {repr(opening_fence)}")
    print(f"  Code content: {repr(code_content)}")  
    print(f"  Closing fence: {repr(closing_fence)}")
    
    # Extract newline character
    newline_char_match = re.search(r"(\r\n|\n|\r)$", opening_fence)
    newline_char = newline_char_match.group(0) if newline_char_match else '\\n'
    print(f"  Newline char: {repr(newline_char)}")
    
    # Get content without newline
    content_of_opening_fence_line = opening_fence[:-len(newline_char)]
    print(f"  Opening fence line: {repr(content_of_opening_fence_line)}")
    
    # Add CodeID
    id_tag_display = f" [CodeID: 1]"
    modified_opening_fence = content_of_opening_fence_line.rstrip() + id_tag_display + newline_char
    print(f"  Modified opening fence: {repr(modified_opening_fence)}")
    
    # Reconstruct
    reconstructed = modified_opening_fence + code_content + closing_fence
    print(f"  Reconstructed block: {repr(reconstructed)}")
    
    print(f"  Reconstructed block (display):")
    print(reconstructed)
