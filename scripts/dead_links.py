#!/usr/bin/env python3
import os
import re
import sys
import argparse
import uuid

def is_valid_uuid(val):
    """
    Check if a string is a valid UUID
    
    Args:
        val (str): String to check
        
    Returns:
        bool: True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def find_dead_links(directory):
    """
    Find files with dead markdown links in a directory
    
    Args:
        directory (str): Path to the directory to scan
        
    Returns:
        dict: Dictionary mapping filenames to lists of dead links
    """
    # Get all markdown files in the directory
    all_files = set()
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            all_files.add(filename)
    
    # Regular expression to find markdown links
    # Pattern: [any text](filename.md)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+\.md)\)')
    
    # Dictionary to store files with dead links
    files_with_dead_links = {}
    
    # Scan each file for links
    for filename in all_files:
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all links in the file
            dead_links = []
            for match in link_pattern.finditer(content):
                link_text = match.group(1)
                link_target = match.group(2)
                
                # Check if the link target is a local file (not a URL)
                if not link_target.startswith(('http://', 'https://', 'ftp://')):
                    # Extract just the filename if it's a path
                    target_filename = os.path.basename(link_target)
                    
                    # Check if it's a UUID.md file
                    if target_filename.endswith('.md'):
                        uuid_part = target_filename[:-3]  # Remove .md extension
                        if is_valid_uuid(uuid_part) or len(uuid_part) > 8:  # Heuristic for UUID-like strings
                            # Check if the target file exists
                            if target_filename not in all_files:
                                dead_links.append(target_filename)
            
            # If there are dead links, add to the dictionary
            if dead_links:
                files_with_dead_links[filename] = dead_links
                
        except Exception as e:
            print(f"Error processing file {filename}: {e}", file=sys.stderr)
    
    return files_with_dead_links

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Find files with dead markdown links in a directory'
    )
    parser.add_argument('directory', help='Path to the directory to scan')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='Show detailed information about dead links')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if the directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory", file=sys.stderr)
        return 1
    
    # Find files with dead links
    files_with_dead_links = find_dead_links(args.directory)
    
    # Print results
    if files_with_dead_links:
        print(f"Found {len(files_with_dead_links)} files with dead links:")
        for filename, dead_links in files_with_dead_links.items():
            if args.verbose:
                print(f"  {filename}:")
                for link in dead_links:
                    print(f"    - {link}")
            else:
                print(f"  {filename}")
        
        # Return non-zero exit code to indicate dead links were found
        return 1
    else:
        print("No dead links found.")
        return 0

if __name__ == "__main__":
    sys.exit(main())