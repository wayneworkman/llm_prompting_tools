# /home/wayne/git/llm_prompting_tools/python_unittest_tool/dependency_tracker.py

"""
Module for tracking function dependencies across Python files.
"""
import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, Dict, List, Optional, Tuple
from collections import defaultdict

# Add import:
from python_unittest_tool.project_indexer import ProjectIndexer

logger = logging.getLogger(__name__)


@dataclass
class FunctionNode:
    """Container for function information."""
    name: str
    file_path: str
    class_name: Optional[str] = None
    source_code: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    dependencies: Set[Tuple[str, Optional[str]]] = field(default_factory=set)


class DependencyTracker:
    """Tracks function dependencies across Python files."""
    
    def __init__(self, project_root: str):
        """
        Initialize DependencyTracker.
        
        Args:
            project_root: The root directory of the project, used for resolving imports
        """
        self.project_root = Path(project_root).resolve()
        
        # NEW: Make a project indexer that has a self.module_map
        self.indexer = ProjectIndexer(str(self.project_root))
        
        self.file_cache: Dict[str, str] = {}
        self.import_map: Dict[str, Dict[str, Tuple[str, Optional[str]]]] = defaultdict(dict)
    
    def track_dependencies(self, start_file: str, start_function: str, start_class: Optional[str] = None) -> List[FunctionNode]:
        """
        Track dependencies starting from a specific function in a given file.
        """
        # Convert to absolute path
        start_file = str(Path(start_file).resolve())
        
        visited = set()
        result = []
        
        self._build_import_map(start_file)
        
        self._track_function_deps(
            file_path=start_file,
            function_name=start_function,
            class_name=start_class,
            visited=visited,
            result=result
        )
        
        return result
    
    def _track_function_deps(
        self,
        file_path: str,
        function_name: str,
        class_name: Optional[str],
        visited: Set[Tuple[str, str, Optional[str]]],
        result: List[FunctionNode]
    ) -> None:
        """
        Analyzes the specified (file_path, function_name, class_name) to find its dependencies,
        recurses on each one, then appends the corresponding FunctionNode at the end. This
        ensures 'helper' and 'local_func' appear before 'main_function' in the 'result'.
        """
        key = (file_path, function_name, class_name)
        if key in visited:
            return
        visited.add(key)

        # Build or update the import map for this file
        self._build_import_map(file_path)

        # Read the file from cache (or skip if missing)
        if file_path not in self.file_cache:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.file_cache[file_path] = f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return

        source = self.file_cache[file_path]
        try:
            tree = ast.parse(source)
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return

        # Use a FunctionAnalyzer to locate the function and gather dependencies
        visitor = FunctionAnalyzer(function_name, class_name, source)
        visitor.visit(tree)

        if not visitor.found_function:
            logger.warning(f"Function {function_name} not found in {file_path}")
            return

        # For each dependency, figure out where it comes from, then recurse
        for dep_name, dep_class in visitor.dependencies:
            resolved_file, resolved_func_name, resolved_class = self._resolve_dependency(
                current_file=file_path,
                function_name=dep_name,
                class_name=dep_class
            )
            if resolved_file:
                self._track_function_deps(
                    resolved_file,
                    resolved_func_name,
                    resolved_class,
                    visited,
                    result
                )

        # Finally, create our FunctionNode and append it
        node = FunctionNode(
            name=function_name,
            file_path=file_path,
            class_name=class_name,
            source_code=visitor.source_code,
            start_line=visitor.start_line,
            end_line=visitor.end_line,
            dependencies=visitor.dependencies
        )
        result.append(node)
    
    def _build_import_map(self, file_path: str) -> None:
        """Parse 'file_path', build an import->(real_file, real_class) map."""
        if file_path in self.import_map:
            return  # Already built
        
        # Ensure file content
        if file_path not in self.file_cache:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.file_cache[file_path] = f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return
        
        source = self.file_cache[file_path]
        try:
            tree = ast.parse(source)
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return
        
        builder = ImportMapBuilder(self.indexer, file_path)
        builder.visit(tree)
        self.import_map[file_path].update(builder.import_map)
    
    def _resolve_dependency(
        self,
        current_file: str,
        function_name: str,
        class_name: Optional[str]
    ) -> Tuple[Optional[str], str, Optional[str]]:
        # If 'function_name' is in the import_map of current_file, we get the real file
        if current_file in self.import_map and function_name in self.import_map[current_file]:
            real_file, real_class = self.import_map[current_file][function_name]
            return real_file, function_name, real_class
        
        return current_file, function_name, class_name


class FunctionAnalyzer(ast.NodeVisitor):
    """AST visitor that locates a specific function and extracts dependencies."""
    
    def __init__(self, target_function: str, target_class: Optional[str], full_source: str):
        self.target_function = target_function
        self.target_class = target_class
        self.full_source = full_source
        
        self.current_class: Optional[str] = None
        self.found_function = False
        self.dependencies: Set[Tuple[str, Optional[str]]] = set()
        
        self.source_code: Optional[str] = None
        self.start_line = 0
        self.end_line = 0
        
        self.var_class_map: Dict[str, str] = {}
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name == self.target_function and self.current_class == self.target_class:
            self.found_function = True
            self.start_line = node.lineno
            self.end_line = node.end_lineno or node.lineno
            
            # Extract code
            import ast
            self.source_code = ast.get_source_segment(self.full_source, node, padded=True)
            
            self.generic_visit(node)
        else:
            self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        # If we do "var = helper()" => var_class_map[var] = "helper"
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                self.var_class_map[var_name] = node.value.func.id
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        if self.found_function:
            if isinstance(node.func, ast.Name):
                # e.g. "helper()" => (helper, None)
                self.dependencies.add((node.func.id, None))
            elif isinstance(node.func, ast.Attribute):
                # e.g. var_name.method_name()
                if isinstance(node.func.value, ast.Name):
                    var_name = node.func.value.id
                    method_name = node.func.attr
                    if var_name in self.var_class_map:
                        # e.g. self.var_class_map["h"] = "Helper"
                        self.dependencies.add((method_name, self.var_class_map[var_name]))
                    else:
                        self.dependencies.add((method_name, var_name))
        self.generic_visit(node)


class ImportMapBuilder(ast.NodeVisitor):
    """
    AST visitor that identifies import statements, calling ProjectIndexer to map them
    to actual file paths, then storing them in import_map as symbol->(real_file, real_class).
    """
    def __init__(self, indexer: ProjectIndexer, current_file: str):
        self.indexer = indexer
        self.current_file = Path(current_file).resolve()
        self.import_map: Dict[str, Tuple[str, Optional[str]]] = {}
    
    def visit_Import(self, node: ast.Import) -> None:
        """
        e.g. import utils => 'utils' -> /project/utils.py
        e.g. import utils as ut => 'ut' -> /project/utils.py
        """
        for name in node.names:
            imported_as = name.asname or name.name
            # If name.name == 'utils', we do indexer.resolve_module(...)
            possible_path = self.indexer.resolve_module(str(self.current_file), name.name, level=0)
            if possible_path:
                self.import_map[imported_as] = (possible_path, None)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """
        e.g. from utils import helper => 'helper' -> /project/utils.py
        e.g. from .local_module import local_func => 'local_func'-> /project/local_module.py
        """
        module_str = node.module or ''
        # level means how many dots => node.level
        # We ask the indexer
        possible_path = self.indexer.resolve_module(str(self.current_file), module_str, node.level)
        if possible_path:
            for alias in node.names:
                imported_as = alias.asname or alias.name
                self.import_map[imported_as] = (possible_path, None)
        self.generic_visit(node)
