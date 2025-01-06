import os
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

def find_gitignore_file(start_dir):
    """
    Search for a .gitignore file by traversing up the directory tree.
    Stop searching if a .git directory is found or if a permission error occurs.
    
    Args:
        start_dir (str): Starting directory path for the search
        
    Returns:
        tuple: (gitignore_path, repo_root)
            - gitignore_path: Full path to found .gitignore file, or None if not found
            - repo_root: Directory containing .gitignore or .git, or None if neither found
    """
    current_dir = os.path.abspath(start_dir)
    
    while True:
        try:
            # Check for .gitignore first
            gitignore_path = os.path.join(current_dir, '.gitignore')
            if os.path.isfile(gitignore_path):
                return gitignore_path, current_dir
            
            # If no .gitignore, check for .git directory
            git_dir = os.path.join(current_dir, '.git')
            if os.path.isdir(git_dir):
                # We're at repo root but no .gitignore exists
                return None, current_dir
            
            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # We've reached the root directory
                return None, None
                
            current_dir = parent_dir
            
        except PermissionError:
            # If we hit a permission error, stop searching
            return None, None

def load_gitignore_spec(root_dir):
    """
    Load the .gitignore file by searching up the directory tree from root_dir.
    Returns a PathSpec object that supports Git's wildmatch patterns.
    
    Args:
        root_dir (str): Starting directory to begin search for .gitignore
        
    Returns:
        PathSpec: PathSpec object containing gitignore patterns
    """
    gitignore_path, _ = find_gitignore_file(root_dir)
    lines = []
    
    if gitignore_path:
        try:
            with open(gitignore_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.read().splitlines()
        except (PermissionError, IOError):
            # If we can't read the file, treat it as empty
            pass
    
    # Create the PathSpec from lines using GitWildMatchPattern
    return PathSpec.from_lines(GitWildMatchPattern, lines)

def should_include_file(path, root_dir, gitignore_spec):
    """
    Return True if `path` is NOT excluded by .gitignore or .git directory.
    We exclude anything inside a .git folder and anything matched by `gitignore_spec`.
    
    Args:
        path (str): Path to the file/directory to check
        root_dir (str): Root directory for relative path calculation
        gitignore_spec (PathSpec): PathSpec object containing gitignore patterns
        
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