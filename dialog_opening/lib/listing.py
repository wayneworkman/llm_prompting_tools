# lib/listing.py (place in ./lib/listing.py)
import os
from lib.gitignore_utils import should_include_file
from lib.file_info import format_file_line

def recursive_list(root_dir, root_path, gitignore_spec):
    """
    Recursively list directories and files.
    Returns a list of lines that represent the directory listing.
    """
    entries = get_directory_entries(root_dir, root_path, gitignore_spec)
    lines = format_directory_listing(root_dir, root_path, entries)
    lines += recurse_into_subdirectories(root_dir, root_path, gitignore_spec, entries)
    return lines

def get_directory_entries(root_dir, root_path, gitignore_spec):
    """
    Get directory entries that should be included.
    Handles PermissionError by returning an empty list (skip).
    """
    entries = []
    try:
        with os.scandir(root_dir) as it:
            for entry in it:
                full_path = os.path.join(root_dir, entry.name)
                if not should_include_file(full_path, root_path, gitignore_spec):
                    continue
                entries.append(entry)
    except PermissionError:
        # If we can't read this directory, skip it entirely
        return []

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

def recurse_into_subdirectories(root_dir, root_path, gitignore_spec, entries):
    """Recursively list directories within the given entries."""
    lines = []
    for e in reversed(entries):
        if e.is_dir(follow_symlinks=False):
            full_path = os.path.join(root_dir, e.name)
            # Double-check we still include this directory
            if should_include_file(full_path, root_path, gitignore_spec):
                sub_lines = recursive_list(full_path, root_path, gitignore_spec)
                if sub_lines:
                    lines.extend(sub_lines)
    return lines
