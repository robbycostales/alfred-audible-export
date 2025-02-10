#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List
import sys
import logging
import json
import os

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
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    def parse_chapters(self, chapter_text: str) -> List[Chapter]:
        """Parse chapter information from text format"""
        chapters = []
        cumulative_time = 0
        
        lines = [line.strip() for line in chapter_text.strip().split("\n") if line.strip()]
        i = 0
        while i < len(lines):
            # Skip empty lines
            if not lines[i]:
                i += 1
                continue
                
            # Get chapter name
            name = lines[i]
            i += 1
            
            # Get duration if next line exists
            if i < len(lines):
                try:
                    duration = self.time_to_seconds(lines[i])
                    chapter = Chapter(
                        name=name,
                        duration_seconds=duration,
                        start_time=cumulative_time
                    )
                    chapters.append(chapter)
                    cumulative_time += duration
                    i += 1
                except (ValueError, IndexError):
                    # If we can't parse the time, assume it's another chapter name
                    continue
            
        return chapters

    def find_chapter_for_timestamp(self, timestamp_seconds: int, chapters: List[Chapter]) -> tuple[int, Chapter]:
        """Find which chapter a timestamp belongs to based on cumulative time"""
        for idx, chapter in enumerate(chapters):
            chapter_end = chapter.start_time + chapter.duration_seconds
            if chapter.start_time <= timestamp_seconds < chapter_end:
                return idx, chapter
        return -1, None

    def parse_bookmarks(self, bookmark_text: str, chapters: List[Chapter]) -> List[Bookmark]:
        """Parse bookmark information from text format"""
        bookmarks = []
        lines = [line.strip() for line in bookmark_text.strip().split("\n") if line.strip()]
        i = 0
        
        while i < len(lines):
            try:
                # Parse bookmark line
                loc_line = lines[i]
                if "[Go to bookmark]" in loc_line:
                    i += 1
                    continue
                    
                # Split on last occurrence of " / " in case chapter name contains " / "
                if " / " not in loc_line:
                    i += 1
                    continue
                    
                chapter_parts = loc_line.rsplit(" / ", 1)
                if len(chapter_parts) != 2:
                    i += 1
                    continue
                    
                input_chapter_name, timestamp = chapter_parts
                timestamp = timestamp.strip()
                
                # Convert timestamp to seconds
                position_seconds = self.time_to_seconds(timestamp)
                
                # Find which chapter this timestamp belongs to
                chapter_index, chapter = self.find_chapter_for_timestamp(position_seconds, chapters)
                if chapter_index == -1:
                    logging.warning(f"Could not find chapter for timestamp {timestamp}")
                    i += 1
                    continue
                
                # Calculate percentage through chapter
                chapter_relative_position = position_seconds - chapter.start_time
                percentage = (chapter_relative_position / chapter.duration_seconds) * 100
                
                # Parse date/time
                i += 1
                if i >= len(lines):
                    break
                date_line = lines[i].strip()
                date_parts = date_line.split(" | ")
                if len(date_parts) != 2:
                    i += 1
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
                    note = note.strip(" \"")
                    i += 2
                
                bookmark = Bookmark(
                    chapter_name=chapter.name,
                    chapter_index=chapter_index,
                    timestamp=timestamp,
                    position_seconds=position_seconds,
                    percentage=percentage,
                    date=date,
                    time=time,
                    note=note
                )
                
                logging.debug(f"Time {timestamp} ({position_seconds}s) assigned to chapter {chapter.name} " +
                            f"(starts at {chapter.start_time}s, duration {chapter.duration_seconds}s)")
                
                bookmarks.append(bookmark)
                
            except Exception as e:
                logging.error(f"Error parsing bookmark at line {i}: {e}")
                i += 1
        
        return sorted(bookmarks, key=lambda x: x.position_seconds)

    def format_output(self, bookmarks: List[Bookmark], base_link: str) -> str:
        """Format bookmarks into Markdown with chapter headers and links"""
        output = []
        current_chapter = None
        
        for bookmark in bookmarks:
            # Add chapter header if new chapter
            if current_chapter != bookmark.chapter_name:
                output.append(f"\n\n#### {bookmark.chapter_name}")
                current_chapter = bookmark.chapter_name
            
            # Create link with position
            link = (f"{base_link.split('&bookmarkPos')[0]}"
                   f"&bookmarkPos={bookmark.position_seconds * 1000}"
                   f"&chapterIndex={bookmark.chapter_index}#")
            
            # Format bookmark line
            line = (f"\n- [{bookmark.timestamp} {int(bookmark.percentage)}%]({link}) - "
                   f"{bookmark.note}")
            output.append(line)
        
        return "".join(output)

def main():
    """Main entry point for Alfred workflow"""
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: script.py '{clipboard:2}xXx{clipboard:1}xXx{clipboard:0}'\n")
        sys.exit(1)

    try:
        # Log input for debugging
        sys.stderr.write(f"Input received: {repr(sys.argv[1])}\n")
        
        # Split input on xXx separator
        clipboard_items = sys.argv[1].split('xXx')
        
        if len(clipboard_items) != 3:
            sys.stderr.write("Error: Need exactly 3 clipboard items separated by 'xXx'\n")
            sys.exit(1)

        # Items passed as input like this
        # {clipboard:2}xXx            (1st copy: the base link)
        # {clipboard:1}xXx            (2nd copy: the chapters)
        # {clipboard:0}               (3rd copy: the bookmarks)
            
        # Get items in correct order
        base_link = clipboard_items[0].strip()
        chapters_text = clipboard_items[1].strip()    
        bookmarks_text = clipboard_items[2].strip()
        
        # Log items for debugging
        sys.stderr.write(f"\nChapters text: {repr(chapters_text[:10])}\n")
        sys.stderr.write(f"\n\nBookmarks text: {repr(bookmarks_text[:10])}\n")
        sys.stderr.write(f"\n\nBase link: {repr(base_link[:10])}\n")
        
        # Initialize parser
        parser = AudibleParser(debug=True)
        
        # Process the data
        chapters = parser.parse_chapters(chapters_text)
        sys.stderr.write(f"\nParsed {len(chapters)} chapters\n")
        
        bookmarks = parser.parse_bookmarks(bookmarks_text, chapters)
        sys.stderr.write(f"Parsed {len(bookmarks)} bookmarks\n")
        
        output = parser.format_output(bookmarks, base_link)
        sys.stderr.write(f"Generated output length: {len(output)}\n")
        
        # Write output to stdout for Alfred
        print(output)
        return 0
        
    except Exception as e:
        sys.stderr.write(f"Error processing clipboard items: {e}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
