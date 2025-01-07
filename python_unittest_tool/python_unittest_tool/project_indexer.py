"""
Module for indexing Python files within a project, mapping module names to file paths.
"""

import os
from pathlib import Path
from typing import Dict, Optional

class ProjectIndexer:
    """
    Scans a project directory for all .py files and builds a map of top-level module names
    (and submodules) to absolute file paths. Also helps with relative imports like '.local_module'.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        # Maps "utils" -> "/project/utils.py", "local_module" -> "/project/local_module.py", etc.
        self.module_map: Dict[str, Path] = {}
        
        self._scan_project(self.project_root)
    
    def _scan_project(self, root: Path) -> None:
        """
        Recursively scan for all .py files under 'root' and build the module_map.
        """
        for dirpath, dirs, files in os.walk(root):
            dirpath_obj = Path(dirpath)
            for filename in files:
                if filename.endswith(".py"):
                    # e.g. /project/utils.py
                    file_path = dirpath_obj / filename
                    # Let's convert /project/utils.py -> "utils"
                    # or /project/subdir/foo.py -> "subdir.foo"
                    # We do this by relative path from project_root
                    rel_path = file_path.relative_to(self.project_root)
                    # e.g. utils.py or subdir/foo.py
                    parts = list(rel_path.with_suffix('').parts)
                    # join with '.' => subdir.foo
                    module_name = ".".join(parts)
                    self.module_map[module_name] = file_path.resolve()
    
    def resolve_module(self, base_file: str, module_str: str, level: int) -> Optional[str]:
        """
        If 'module_str' is something like 'utils', return '/project/utils.py' if found.
        If it's a relative import (level=1 => '.'), we interpret relative to 'base_file'.
        Returns the absolute path as a string or None if not found.
        """
        base_path = Path(base_file).parent
        # If it's a relative import, go up 'level' times
        for _ in range(level):
            base_path = base_path.parent
        
        if module_str == "":
            # from . import local_func => just the same directory
            # from .. import something => a parent directory
            # base_path might directly point to the folder
            # So, see if there's an __init__.py
            init_candidate = base_path / "__init__.py"
            if init_candidate.exists():
                return str(init_candidate.resolve())
            return None
        
        # If there's a module name, e.g. 'local_module' or 'subdir.module'
        # We'll try combining base_path with module_str
        # Then see if that file is in our module_map
        # e.g. base_path = /project, module_str= local_module => "local_module"
        
        # If module_str has dots: 'subdir.another'
        # we can build that out => subdir/another
        # But let's keep it consistent with how _scan_project stored them
        # because module_map might have "subdir.another" -> /project/subdir/another.py
        
        # We'll do a direct lookup in module_map for the full string
        # or if there's subdir stuff, we keep it as is.
        # But if we want to do "base_path relative" approach, we might do:
        
        # Approach: Attempt (base_path rel to self.project_root) + '.' + module_str
        # Then see if that is in module_map
        try:
            # e.g. base_path = /project, project_root=/project => base_rel=""
            # so we get ".local_module"
            
            base_rel = base_path.relative_to(self.project_root)
            # e.g. base_rel = "." or "subdir"
            
            # If base_rel == ".", we skip it. Otherwise we do "subdir.module"
            if str(base_rel) == ".":
                joined = module_str
            else:
                joined = f"{str(base_rel).replace('/', '.')}.{module_str}"
            
            # Convert any path-ish slashes to dots
            joined = joined.replace("/", ".")
            
            # Now see if we have a direct match in module_map
            if joined in self.module_map:
                return str(self.module_map[joined])
            
            # If not, we can fallback to the raw module_str
            if module_str in self.module_map:
                return str(self.module_map[module_str])
            
            return None
        except ValueError:
            # Means base_path wasn't under project_root or something weird
            return None

