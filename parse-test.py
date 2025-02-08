#!/usr/bin/env python3

import sys
from pathlib import Path
from parse import AudibleParser

def read_file(filepath: str) -> str:
    """Read content from a file, stripping any trailing whitespace"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()

def main():
    # Initialize parser with debug logging
    parser = AudibleParser(debug=True)
    
    try:
        # Read test files
        chapters = read_file('t-chapters.txt')
        bookmarks = read_file('t-bookmarks.txt')
        link = read_file('t-link.txt')
        
        # Process the data
        chapters_data = parser.parse_chapters(chapters)
        
        # Log chapter information for debugging
        print("\nChapter Information:")
        print("=" * 40)
        for i, chapter in enumerate(chapters_data):
            print(f"Chapter {i}: {chapter.name}")
            print(f"  Start: {chapter.start_time}s")
            print(f"  Duration: {chapter.duration_seconds}s")
            print(f"  End: {chapter.start_time + chapter.duration_seconds}s")
            print("-" * 40)
        
        # Process bookmarks
        bookmarks_data = parser.parse_bookmarks(bookmarks, chapters_data)
        
        # Format output
        output = parser.format_output(bookmarks_data, link)
        
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
    main()