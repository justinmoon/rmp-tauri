#!/usr/bin/env python3
import sqlite3
import argparse
import sys
import json
import os
import re
import uuid
import subprocess
import shutil

def setup_virtual_env():
    """
    Set up a virtual environment and install required packages
    """
    try:
        # Check if venv directory exists
        if not os.path.exists('./venv'):
            print("Setting up virtual environment...")
            subprocess.run([sys.executable, '-m', 'venv', './venv'], check=True)
        
        # Determine the pip executable path
        pip_cmd = './venv/bin/pip' if os.name != 'nt' else r'.\venv\Scripts\pip'
        
        # Install required packages
        print("Installing required packages...")
        subprocess.run([pip_cmd, 'install', 'html2text'], check=True)
        
        return True
    except Exception as e:
        print(f"Error setting up virtual environment: {e}", file=sys.stderr)
        return False

def import_html2text():
    """
    Import html2text from the virtual environment
    """
    venv_path = './venv/lib/python{}.{}/site-packages'.format(
        sys.version_info.major, sys.version_info.minor
    )
    if os.name == 'nt':
        venv_path = r'.\venv\Lib\site-packages'
    
    if venv_path not in sys.path:
        sys.path.insert(0, venv_path)
    
    try:
        import html2text
        return html2text
    except ImportError:
        print("Could not import html2text. Using fallback converter.", file=sys.stderr)
        return None

def extract_notes_from_sqlite(db_path, user_id=3):
    """
    Extract notes from SQLite database
    
    Args:
        db_path (str): Path to the SQLite database file
        user_id (int): User ID to filter notes by
        
    Returns:
        list: List of note dictionaries
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute("SELECT id, text FROM notes_note WHERE user_id = ?", (user_id,))
        
        # Fetch all results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        notes = [{"id": row["id"], "text": row["text"]} for row in results]
        
        print(f"Extracted {len(notes)} notes from the database")
        return notes
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}", file=sys.stderr)
        return None
    finally:
        # Close the connection
        if 'conn' in locals():
            conn.close()

def convert_html_to_markdown(notes, html2text_module=None):
    """
    Convert HTML to Markdown in the text field of each note
    
    Args:
        notes (list): List of note dictionaries
        html2text_module: The html2text module to use for conversion
        
    Returns:
        list: Updated list of note dictionaries
    """
    if html2text_module:
        # Use html2text library
        h = html2text_module.HTML2Text()
        h.ignore_links = False  # Keep links in the markdown
        h.body_width = 0  # Don't wrap text
        
        for note in notes:
            if "text" in note and note["text"]:
                note["text"] = h.handle(note["text"]).strip()
    else:
        # Use fallback converter
        for note in notes:
            if "text" in note and note["text"]:
                note["text"] = fallback_html_to_markdown(note["text"])
    
    print(f"Converted HTML to Markdown in {len(notes)} notes")
    return notes

def fallback_html_to_markdown(html):
    """
    Fallback HTML to Markdown converter
    
    Args:
        html (str): HTML string to convert
        
    Returns:
        str: Markdown string
    """
    if not html:
        return ""
    
    # Convert <a> tags to Markdown links
    def replace_link(match):
        href = match.group(1)
        text = match.group(2)
        return f"[{text}]({href})"
    
    markdown = re.sub(r'<a href="([^"]+)">([^<]+)</a>', replace_link, html)
    
    # Remove <p> tags
    markdown = re.sub(r'<p>', '', markdown)
    markdown = re.sub(r'</p>', '', markdown)
    
    # Handle other common HTML tags
    markdown = re.sub(r'<strong>([^<]+)</strong>', r'**\1**', markdown)
    markdown = re.sub(r'<em>([^<]+)</em>', r'*\1*', markdown)
    markdown = re.sub(r'<h1>([^<]+)</h1>', r'# \1', markdown)
    markdown = re.sub(r'<h2>([^<]+)</h2>', r'## \1', markdown)
    markdown = re.sub(r'<h3>([^<]+)</h3>', r'### \1', markdown)
    markdown = re.sub(r'<ul>', '', markdown)
    markdown = re.sub(r'</ul>', '', markdown)
    markdown = re.sub(r'<li>([^<]+)</li>', r'- \1', markdown)
    
    return markdown.strip()

def fix_note_ids(notes):
    """
    Fix note IDs by replacing them with UUIDs and updating references
    
    Args:
        notes (list): List of note dictionaries
        
    Returns:
        list: Updated list of note dictionaries
    """
    # Create a mapping of old IDs to new UUIDs
    id_mapping = {}
    for note in notes:
        if "id" in note:
            old_id = note["id"]
            # Remove .md extension if present for consistent mapping
            old_id_base = old_id.replace(".md", "")
            # Generate a new UUID
            new_id = f"{uuid.uuid4()}.md"
            # Store the mapping
            id_mapping[old_id] = new_id
            id_mapping[old_id_base] = new_id  # Also map the base ID without extension
    
    # Update all note IDs and references in text
    for note in notes:
        # Update the note ID
        if "id" in note:
            old_id = note["id"]
            old_id_base = old_id.replace(".md", "")
            note["id"] = id_mapping.get(old_id, id_mapping.get(old_id_base, old_id))
        
        # Update references in text
        if "text" in note and note["text"]:
            text = note["text"]
            
            # Find all markdown links in the text
            # Pattern: [text](link)
            def replace_link(match):
                link_text = match.group(1)
                link_target = match.group(2)
                
                # Check if the link target is in our mapping
                # Try both with and without .md extension
                new_target = id_mapping.get(link_target, id_mapping.get(link_target.replace(".md", ""), link_target))
                
                return f"[{link_text}]({new_target})"
            
            # Replace all links in the text
            updated_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)
            note["text"] = updated_text
    
    print(f"Fixed IDs for {len(notes)} notes")
    return notes

def export_to_files(notes, output_dir):
    """
    Export notes to individual files
    
    Args:
        notes (list): List of note dictionaries
        output_dir (str): Path to the output directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a file for each note
        file_count = 0
        for note in notes:
            if "id" in note and "text" in note:
                # Get the filename and content
                filename = note["id"]
                content = note["text"]
                
                # Create the file
                file_path = os.path.join(output_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                file_count += 1
        
        print(f"Exported {file_count} notes to individual files in {output_dir}")
        return True
        
    except Exception as e:
        print(f"Error exporting notes: {e}", file=sys.stderr)
        return False

def sqlite_to_fs(db_path, output_dir, temp_dir=None):
    """
    Process SQLite database to filesystem notes
    
    Args:
        db_path (str): Path to the SQLite database file
        output_dir (str): Path to the output directory
        temp_dir (str, optional): Path to store temporary files
        
    Returns:
        int: 0 if successful, non-zero otherwise
    """
    try:
        # Set up virtual environment and import html2text
        setup_success = setup_virtual_env()
        html2text_module = import_html2text() if setup_success else None
        
        # Extract notes from SQLite database
        notes = extract_notes_from_sqlite(db_path)
        if notes is None:
            return 1
        
        # Convert HTML to Markdown
        notes = convert_html_to_markdown(notes, html2text_module)
        
        # Fix note IDs
        notes = fix_note_ids(notes)
        
        # Export to files
        export_success = export_to_files(notes, output_dir)
        if not export_success:
            return 1
        
        print(f"Successfully processed {len(notes)} notes from SQLite to filesystem")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Process SQLite database to filesystem notes'
    )
    parser.add_argument('db_path', help='Path to the SQLite database file')
    parser.add_argument('output_dir', help='Path to the output directory')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Process SQLite database to filesystem notes
    return sqlite_to_fs(args.db_path, args.output_dir)

if __name__ == "__main__":
    sys.exit(main())