#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List, Optional
import sys
import logging
from datetime import datetime

@dataclass
class Chapter:
    """Represents a chapter in the audiobook"""
    name: str
    duration_seconds: int
    start_time: int  # cumulative start time in seconds

@dataclass
class Bookmark:
    """Represents a bookmark/note in the audiobook"""
    chapter_name: str
    chapter_index: int
    timestamp: str
    position_seconds: int
    percentage: float
    date: str
    time: str
    note: str

class AudibleParser:
    def __init__(self, debug: bool = False):
        """Initialize parser with optional debug logging"""
        self.setup_logging(debug)
        
    @staticmethod
    def setup_logging(debug: bool):
        """Configure logging with appropriate level"""
        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    @staticmethod
    def time_to_seconds(time_str: str) -> int:
        """Convert time string (HH:MM:SS or MM:SS) to seconds"""
        parts = time_str.strip().split(":")
        if len(parts) == 2:  # MM:SS format
            parts.insert(0, "0")  # Add 0 hours
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    def parse_chapters(self, chapter_text: str) -> List[Chapter]:
        """Parse chapter information from text format"""
        chapters = []
        cumulative_time = 0
        
        lines = [line.strip() for line in chapter_text.strip().split("\n") if line.strip()]
        i = 0
        while i < len(lines):
            current_line = lines[i]
            next_line = lines[i + 1] if i + 1 < len(lines) else None
            
            # If next line contains time format (MM:SS or HH:MM:SS)
            if next_line and any(next_line.count(":") == count for count in [1, 2]):
                name = current_line
                time_str = next_line
                
                # Convert MM:SS to HH:MM:SS if needed
                if time_str.count(":") == 1:
                    time_str = "00:" + time_str
                    
                duration = self.time_to_seconds(time_str)
                chapter = Chapter(
                    name=name,
                    duration_seconds=duration,
                    start_time=cumulative_time
                )
                chapters.append(chapter)
                cumulative_time += duration
                i += 2  # Skip the time line
            else:
                i += 1
                
            duration = self.time_to_seconds(time_str)
            chapter = Chapter(
                name=name,
                duration_seconds=duration,
                start_time=cumulative_time
            )
            chapters.append(chapter)
            cumulative_time += duration
            
        return chapters

    def parse_bookmarks(self, bookmark_text: str, chapters: List[Chapter]) -> List[Bookmark]:
        """Parse bookmark information from text format"""
        bookmarks = []
        lines = [line.strip() for line in bookmark_text.strip().split("\n") if line.strip()]
        i = 0
        
        while i < len(lines):
            if i >= len(lines):
                break
                
            loc_line = lines[i]
            if "[Go to bookmark]" in loc_line:
                i += 1
                continue
                
            try:
                # Split on last occurrence of " / " in case chapter name contains " / "
                if " / " not in loc_line:
                    i += 1
                    continue
                    
                chapter_parts = loc_line.rsplit(" / ", 1)
                if len(chapter_parts) != 2:
                    i += 1
                    continue
                    
                chapter_name, timestamp = chapter_parts
                chapter_name = chapter_name.strip()
                timestamp = timestamp.strip()
                
                # Find chapter index
                chapter_index = next(
                    (idx for idx, ch in enumerate(chapters) if ch.name == chapter_name),
                    -1
                )
                if chapter_index == -1:
                    logging.warning(f"Chapter not found: {chapter_name}")
                    i += 1
                    continue
                
                # Parse timestamp
                position_seconds = self.time_to_seconds(timestamp)
                
                # Calculate percentage through chapter
                chapter = chapters[chapter_index]
                percentage = ((position_seconds - chapter.start_time) / 
                            chapter.duration_seconds * 100)
                
                # Parse date line
                i += 1
                if i >= len(lines):
                    break
                date_line = lines[i]
                date_parts = date_line.split(" | ")
                if len(date_parts) != 2:
                    continue
                date, time = date_parts
                
                # Parse note
                i += 1
                if i >= len(lines):
                    break
                note = lines[i].strip()
                if "[Go to bookmark]" in note:
                    note = "(blank)"
                    i += 1
                else:
                    note = note.strip(" \"")  # Remove quotes and extra spaces
                    i += 2
                
                bookmark = Bookmark(
                    chapter_name=chapter_name,
                    chapter_index=chapter_index,
                    timestamp=timestamp,
                    position_seconds=position_seconds,
                    percentage=percentage,
                    date=date,
                    time=time,
                    note=note
                )
                bookmarks.append(bookmark)
                
            except Exception as e:
                logging.error(f"Error parsing bookmark at line {i}: {e}")
                i += 1
        
        return list(reversed(bookmarks))  # Reverse to match original order

    def format_output(self, bookmarks: List[Bookmark], base_link: str) -> str:
        """Format bookmarks into Markdown with chapter headers and links"""
        output = []
        current_chapter = None
        
        for bookmark in bookmarks:
            # Add chapter header if new chapter
            if current_chapter != bookmark.chapter_name:
                output.append(f"\n\n#### {bookmark.chapter_name}")
                current_chapter = bookmark.chapter_name
            
            # Create link with position and chapter index
            link = (f"{base_link.split('&bookmarkPos')[0]}"
                   f"&bookmarkPos={bookmark.position_seconds * 1000}"
                   f"&chapterIndex={bookmark.chapter_index}#")
            
            # Format bookmark line with timestamp, percentage, and note
            line = (f"\n- [{bookmark.timestamp} {int(bookmark.percentage)}%]({link}) - "
                   f"{bookmark.note}")
            output.append(line)
        
        return "".join(output)

def main():
    """Main entry point for the script"""
    if len(sys.argv) != 2:
        print("Usage: parse.py 'chapters_text xx\\n bookmarks_text xx\\n base_link'", 
              file=sys.stderr)
        sys.exit(1)

    # Parse input from Alfred (3 parts separated by xx\n)
    chapters_text, bookmarks_text, base_link = sys.argv[1].split("xx\n")
    
    # Initialize parser with debug logging
    parser = AudibleParser(debug=True)
    
    # Process the data
    chapters = parser.parse_chapters(chapters_text)
    bookmarks = parser.parse_bookmarks(bookmarks_text, chapters)
    output = parser.format_output(bookmarks, base_link)
    
    # Write formatted output to stdout (will be captured by Alfred)
    sys.stdout.write(output)

if __name__ == "__main__":
    main()