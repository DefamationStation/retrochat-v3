#!/usr/bin/env python3
"""
Debug script to see exactly what the processed text looks like.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.core.text_processing_utils import _process_text_for_code_blocks

# Exact content from the session file (malformed)
session_content = '''Sure! Here's a simple Python program:

```python [CodeID: 1]# A simple Python program
name = input("Enter your name: ")
print(f"Hello, {name}!")```

Done.'''

print("DEBUG: Character-by-character analysis")
print("=" * 60)

processed_text, found_blocks, next_id = _process_text_for_code_blocks(session_content, 10)

print("PROCESSED TEXT (with visible newlines):")
processed_display = processed_text.replace('\n', '\\n').replace('\r', '\\r')
print(processed_display)

print("\nLOOKING FOR CLOSING FENCE PATTERNS:")
lines = processed_text.split('\n')
for i, line in enumerate(lines):
    if '```' in line:
        print(f"Line {i}: {repr(line)}")

print("\nCHECKING END OF TEXT:")
print(f"Last 20 chars: {repr(processed_text[-20:])}")

if processed_text.endswith('\n```'):
    print("✅ Ends with proper newline + closing fence")
elif processed_text.endswith('```'):
    print("❌ Ends with closing fence but no newline before it")
else:
    print("❓ Unexpected ending")
