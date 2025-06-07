import os
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

def find_ignore_files(start_dir):
    """
    Search for .gitignore and .ignore files by traversing up the directory tree.
    Stop searching if a .git directory is found or if a permission error occurs.
    
    Args:
        start_dir (str): Starting directory path for the search
        
    Returns:
        tuple: (ignore_files, repo_root)
            - ignore_files: List of full paths to found .gitignore/.ignore files
            - repo_root: Directory containing ignore files or .git, or None if neither found
    """
    current_dir = os.path.abspath(start_dir)
    
    while True:
        try:
            ignore_files = []
            
            # Check for .gitignore
            gitignore_path = os.path.join(current_dir, '.gitignore')
            if os.path.isfile(gitignore_path):
                ignore_files.append(gitignore_path)
            
            # Check for .ignore
            ignore_path = os.path.join(current_dir, '.ignore')
            if os.path.isfile(ignore_path):
                ignore_files.append(ignore_path)
            
            # If we found any ignore files, return them
            if ignore_files:
                return ignore_files, current_dir
            
            # If no ignore files, check for .git directory
            git_dir = os.path.join(current_dir, '.git')
            if os.path.isdir(git_dir):
                # We're at repo root but no ignore files exist
                return [], current_dir
            
            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # We've reached the root directory
                return [], None
                
            current_dir = parent_dir
            
        except PermissionError:
            # If we hit a permission error, stop searching
            return [], None

def load_gitignore_spec(root_dir):
    """
    Load .gitignore and .ignore files by searching up the directory tree from root_dir.
    Returns a PathSpec object that supports Git's wildmatch patterns.
    
    Args:
        root_dir (str): Starting directory to begin search for ignore files
        
    Returns:
        PathSpec: PathSpec object containing combined patterns from all ignore files
    """
    ignore_files, _ = find_ignore_files(root_dir)
    all_lines = []
    
    for ignore_file in ignore_files:
        try:
            with open(ignore_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.read().splitlines()
                all_lines.extend(lines)
        except (PermissionError, IOError):
            # If we can't read the file, skip it
            pass
    
    # Create the PathSpec from all combined lines using GitWildMatchPattern
    return PathSpec.from_lines(GitWildMatchPattern, all_lines)

def should_include_file(path, root_dir, gitignore_spec):
    """
    Return True if `path` is NOT excluded by .gitignore/.ignore or .git directory.
    We exclude anything inside a .git folder and anything matched by `gitignore_spec`.
    
    Args:
        path (str): Path to the file/directory to check
        root_dir (str): Root directory for relative path calculation
        gitignore_spec (PathSpec): PathSpec object containing ignore patterns
        
    Returns:
        bool: True if the file should be included, False if it should be excluded
    """
    # Exclude anything within .git
    if '.git' in path.split(os.sep):
        return False

    # Compare relative path to the pathspec
    rel_path = os.path.relpath(path, root_dir).replace('\\', '/')

    # If it's a directory, append trailing slash so 'subdir/' patterns match
    if os.path.isdir(path) and not rel_path.endswith('/'):
        rel_path += '/'

    # If pathspec matches, that means "excluded," so we invert it
    return not gitignore_spec.match_file(rel_path)

# Maintain backward compatibility with old function name
find_gitignore_file = find_ignore_files