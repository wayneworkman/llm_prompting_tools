# lib/gitignore_utils.py (place in ./lib/gitignore_utils.py)

import os
import fnmatch

def load_gitignore_patterns(root_dir):
    """Load .gitignore patterns as a single list, including negation lines with !."""
    gitignore_path = os.path.join(root_dir, '.gitignore')
    patterns = []
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                # Ignore empty lines and comments
                if not line or line.startswith('#'):
                    continue
                patterns.append(line)
    return patterns

def matches_gitignore(path, root_dir, patterns):
    """
    Check if a given path matches any .gitignore pattern.
    Patterns can include negations using '!'.
    The last matching pattern (excluding negation) decides if excluded.
    Negation (!pattern) re-includes files that would otherwise be excluded.
    """
    if not patterns:
        return False

    rel_path = os.path.relpath(path, root_dir)
    rel_path = rel_path.replace('\\', '/')  # Normalize path for matching

    excluded = False
    for pat in patterns:
        is_negation = pat.startswith('!')
        p = pat[1:] if is_negation else pat
        if pattern_matches(p, rel_path):
            if is_negation:
                # Negation flips the state to included
                excluded = False
            else:
                excluded = True

    return excluded

def pattern_matches(pat, rel_path):
    """Check if a single pattern matches the relative path."""
    # If the pattern ends with '/', it matches a directory and its contents
    if pat.endswith('/'):
        dir_pattern = pat.rstrip('/')
        if rel_path == dir_pattern or rel_path.startswith(dir_pattern + '/'):
            return True
    elif pat.startswith('/'):
        anchor_pat = pat.lstrip('/')
        if fnmatch.fnmatch(rel_path, anchor_pat):
            return True
    else:
        if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(os.path.basename(rel_path), pat):
            return True
    return False

def should_include_file(path, root_dir, gitignore_patterns):
    """Determine if a file or directory should be included based on gitignore and .git filtering."""
    if '.git' in path.split(os.sep):
        return False
    if not gitignore_patterns:
        # If no patterns given, treat as no exclusion
        return True
    return not matches_gitignore(path, root_dir, gitignore_patterns)
