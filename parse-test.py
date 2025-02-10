#!/usr/bin/env python3

import sys
from pathlib import Path
from parse import main as parse_main

def read_file(filepath: str) -> str:
    """Read content from a file, stripping any trailing whitespace"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()

def main():
    try:
        # Read test files
        chapters = read_file('test-input/t-chapters.txt')
        bookmarks = read_file('test-input/t-bookmarks.txt')
        link = read_file('test-input/t-link.txt')
        
        # Format the input string as expected by parse.py
        input_str = f"{chapters}xXx{bookmarks}xXx{link}"
        
        # Capture stdout to get the markdown output
        original_stdout = sys.stdout
        sys.stdout = output_capture = StringIO()
        
        # Call parse.py's main with our formatted input
        sys.argv = ['parse.py', input_str]
        parse_main()
        
        # Restore stdout and get captured output
        sys.stdout = original_stdout
        output = output_capture.getvalue()
        
        # Write to file
        output_file = Path('test-output.md')
        output_file.write_text(output)
        print(f"\nOutput written to {output_file}")
        
        # Print preview
        print("\nOutput preview:")
        print("=" * 40)
        preview = output[:500] + "..." if len(output) > 500 else output
        print(preview)
        print("=" * 40)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    from io import StringIO
    main()
