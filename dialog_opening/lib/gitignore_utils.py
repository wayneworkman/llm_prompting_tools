# lib/gitignore_utils.py (place in ./lib/gitignore_utils.py)

import os
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

def load_gitignore_spec(root_dir):
    """
    Load the .gitignore file at `root_dir` into a PathSpec object
    that supports Git's wildmatch patterns (including negations, etc.).
    """
    gitignore_path = os.path.join(root_dir, '.gitignore')
    lines = []
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()

    # Create the PathSpec from lines using GitWildMatchPattern
    return PathSpec.from_lines(GitWildMatchPattern, lines)

def should_include_file(path, root_dir, gitignore_spec):
    """
    Return True if `path` is NOT excluded by .gitignore or .git directory.
    We exclude anything inside a .git folder and anything matched by `gitignore_spec`.
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

