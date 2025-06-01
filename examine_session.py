#!/usr/bin/env python3
"""
Script to examine session file content and identify code block patterns.
"""

import json
import re
import os

def examine_session_file():
    session_path = r"C:\Users\frenz\AppData\Roaming\Retrochat\sessions\session_ec79637a-4118-4559-9006-9d56ec58aed1.json"
    
    if not os.path.exists(session_path):
        print(f"Session file not found: {session_path}")
        return
    
    with open(session_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Examining conversation history for code blocks...")
    
    for i, message in enumerate(data.get('conversation_history', [])):
        content = message.get('content', '')
        if '```' in content:
            print(f"\n{'='*60}")
            print(f"Message {i+1} ({message.get('role', 'unknown')}):")
            print(f"{'='*60}")
            print(repr(content))
            
            # Look for specific patterns
            code_blocks = re.findall(r'```[^`]*```', content, re.DOTALL)
            print(f"\nFound {len(code_blocks)} code block(s):")
            for j, block in enumerate(code_blocks):
                print(f"  Block {j+1}: {repr(block[:100])}...")

if __name__ == "__main__":
    examine_session_file()
