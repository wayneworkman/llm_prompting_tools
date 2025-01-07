# python_unittest_tool/project_indexer.py
# (This file goes in the python_unittest_tool/ directory.)

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
                    file_path = dirpath_obj / filename
                    # Convert /project/utils.py -> "utils", etc.
                    rel_path = file_path.relative_to(self.project_root)
                    parts = list(rel_path.with_suffix('').parts)
                    module_name = ".".join(parts)
                    self.module_map[module_name] = file_path.resolve()
    
    def resolve_module(self, base_file: str, module_str: str, level: int) -> Optional[str]:
        """
        If 'module_str' is something like 'utils', return '/project/utils.py' if found.
        If it's a relative import (level=1 => '.'), we interpret that as the same dir as base_file.
        Returns the absolute path as a string or None if not found.
        """
        base_path = Path(base_file).parent
        
        # Adjust base_path by (level - 1) so that:
        #   level=1 => no upward movement (same directory)
        #   level=2 => go up one directory, etc.
        up_steps = max(0, level - 1)
        for _ in range(up_steps):
            base_path = base_path.parent
        
        if module_str == "":
            # from . import local_func => base_path is the same dir
            init_candidate = base_path / "__init__.py"
            if init_candidate.exists():
                return str(init_candidate.resolve())
            return None
        
        try:
            base_rel = base_path.relative_to(self.project_root)
            if str(base_rel) == ".":
                joined = module_str
            else:
                joined = f"{str(base_rel).replace('/', '.')}.{module_str}"
            joined = joined.replace("/", ".")
            
            if joined in self.module_map:
                return str(self.module_map[joined])
            
            if module_str in self.module_map:
                return str(self.module_map[module_str])
            
            return None
        except ValueError:
            return None
