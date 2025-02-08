#!/usr/bin/env python3

import sys
from pathlib import Path
from parse import AudibleParser

def read_file(filepath: str) -> str:
    """Read content from a file, stripping any trailing whitespace"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()

def main():
    # Read test files
    chapters = read_file('t-chapters.txt')
    bookmarks = read_file('t-bookmarks.txt')
    link = read_file('t-link.txt')

    # Combine into Alfred-style input
    alfred_input = f"{chapters}xx\n{bookmarks}xx\n{link}"

    # Initialize parser
    parser = AudibleParser(debug=True)
    
    # Process the data
    chapters_data = parser.parse_chapters(chapters)
    bookmarks_data = parser.parse_bookmarks(bookmarks, chapters_data)
    output = parser.format_output(bookmarks_data, link)
    
    # Write output to file
    output_file = Path('test-output.md')
    output_file.write_text(output)
    print(f"Output written to {output_file}")

    # Also print to console for immediate feedback
    print("\nOutput preview:")
    print("=" * 40)
    print(output[:500] + "..." if len(output) > 500 else output)
    print("=" * 40)

if __name__ == "__main__":
    main()