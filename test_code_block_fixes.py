#!/usr/bin/env python3
"""
Test script to verify that the code block fixes work correctly for both
properly formatted and malformed markdown code blocks.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrochat_app.core.text_processing_utils import _process_text_for_code_blocks
from retrochat_app.core.code_block_utils import CODE_BLOCK_PATTERN
import re

def test_case(name, input_text, expected_blocks_count):
    """Test a specific case and report results."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"INPUT:\n{repr(input_text)}")
    
    # Test the processing function
    try:
        processed_text, found_blocks, next_id = _process_text_for_code_blocks(input_text, 1)
        print(f"\nPROCESSED TEXT:\n{repr(processed_text)}")
        print(f"\nFOUND BLOCKS: {len(found_blocks)}")
        for block_id, content in found_blocks.items():
            print(f"  Block {block_id}: {repr(content)}")
        print(f"NEXT ID: {next_id}")
        
        # Test the regex pattern
        matches = list(CODE_BLOCK_PATTERN.finditer(processed_text))
        print(f"\nREGEX MATCHES: {len(matches)}")
        for i, match in enumerate(matches):
            print(f"  Match {i+1}: language='{match.group(1)}', code_id='{match.group(2)}', content='{match.group(3)[:50]}...'")
        
        # Verify expected count
        if len(found_blocks) == expected_blocks_count:
            print(f"\n✅ SUCCESS: Found {expected_blocks_count} blocks as expected")
        else:
            print(f"\n❌ FAILED: Expected {expected_blocks_count} blocks, got {len(found_blocks)}")
        
        # Verify regex can extract the processed blocks
        if len(matches) == expected_blocks_count:
            print(f"✅ SUCCESS: Regex extracted {expected_blocks_count} blocks as expected")
        else:
            print(f"❌ FAILED: Regex expected {expected_blocks_count} blocks, got {len(matches)}")
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("Testing Code Block Processing Fixes")
    print("=" * 60)
    
    # Test 1: Properly formatted code block
    test_case(
        "Properly formatted code block",
        "Here's some code:\n```python\nprint('hello')\n```\nDone.",
        1
    )
    
    # Test 2: Malformed code block (missing newline after opening fence)
    test_case(
        "Malformed: missing newline after opening fence",
        "```python [CodeID: 1]# This is malformed\nprint('hello')\n```",
        1
    )
    
    # Test 3: Malformed code block (missing newline before closing fence)
    test_case(
        "Malformed: missing newline before closing fence", 
        "```python\nprint('hello')```",
        1
    )
    
    # Test 4: Completely malformed (no newlines)
    test_case(
        "Completely malformed: no newlines",
        "```pythonprint('hello')```",
        1
    )
    
    # Test 5: Multiple code blocks (mixed format)
    test_case(
        "Multiple blocks: mixed format",
        "```python\nprint('good')\n```\n\nSome text\n\n```python [CodeID: 5]print('bad')\n```",
        2
    )
    
    # Test 6: Existing session-like content (from actual session file)
    test_case(
        "Session-like content",
        "I'll create a simple function for you:\n\n```python [CodeID: 1]def greet(name):\n    return f\"Hello, {name}!\"\n\nprint(greet(\"World\"))\n```\n\nThis function takes a name and returns a greeting.",
        1
    )
    
    # Test 7: Edge case - code block with no language
    test_case(
        "No language specified",
        "```\nsome code\n```",
        1
    )
    
    # Test 8: Edge case - code block with existing CodeID (should get new ID)
    test_case(
        "Existing CodeID should get new ID",
        "```python [CodeID: 999]\nprint('existing')\n```",
        1
    )

if __name__ == "__main__":
    main()
