# lib/listing.py (place in ./lib/listing.py)

import os
from lib.gitignore_utils import should_include_file
from lib.file_info import format_file_line

def recursive_list(root_dir, root_path, gitignore_patterns):
    """
    Recursively list directories and files.
    Returns a list of lines that represent the directory listing.
    """
    # Ensure gitignore_patterns is a list. If empty or None, just use empty list.
    if not gitignore_patterns:
        gitignore_patterns = []
    entries = get_directory_entries(root_dir, root_path, gitignore_patterns)
    lines = format_directory_listing(root_dir, root_path, entries)
    lines += recurse_into_subdirectories(root_dir, root_path, gitignore_patterns, entries)
    return lines

def get_directory_entries(root_dir, root_path, gitignore_patterns):
    """Get directory entries that should be included."""
    entries = []
    with os.scandir(root_dir) as it:
        for entry in it:
            full_path = os.path.join(root_dir, entry.name)
            if not should_include_file(full_path, root_path, gitignore_patterns):
                continue
            entries.append(entry)
    # Sort by modification time (newest first)
    entries.sort(key=lambda e: e.stat(follow_symlinks=False).st_mtime, reverse=True)
    return entries

def format_directory_listing(root_dir, root_path, entries):
    """Format the directory header and file lines."""
    lines = []
    if root_dir != root_path:
        rel_dir = os.path.relpath(root_dir, root_path)
        lines.append(f"{rel_dir}:")
    else:
        lines.append(f"{os.path.abspath(root_dir)}:")

    total_blocks = sum(getattr(e.stat(follow_symlinks=False), 'st_blocks', 0) for e in entries)
    lines.append(f"total {total_blocks}")

    for e in entries:
        st = e.stat(follow_symlinks=False)
        line = format_file_line(os.path.join(root_dir, e.name), st)
        lines.append(line)
    lines.append("")
    return lines

def recurse_into_subdirectories(root_dir, root_path, gitignore_patterns, entries):
    """Recursively list directories within the given entries."""
    lines = []
    for e in reversed(entries):
        if e.is_dir(follow_symlinks=False):
            full_path = os.path.join(root_dir, e.name)
            if should_include_file(full_path, root_path, gitignore_patterns):
                sub_lines = recursive_list(full_path, root_path, gitignore_patterns)
                if sub_lines:
                    lines.extend(sub_lines)
    return lines
