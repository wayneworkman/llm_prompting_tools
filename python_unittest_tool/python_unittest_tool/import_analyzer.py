"""
Module for analyzing and extracting used imports from Python code.
(Treat any import from the same module as used once any name is used.)
"""
import ast
from dataclasses import dataclass, field
from typing import Set, Dict, List, Optional
from pathlib import Path

@dataclass
class ImportInfo:
    """Container for import information."""
    import_statement: str  # The original import statement
    module_name: str       # The module being imported
    names: Set[str]        # Names being imported
    is_used: bool = False
    alias_map: Dict[str, str] = field(default_factory=dict)  # Maps aliases to original names


class ImportAnalyzer:
    """Analyzes Python code to determine which imports are actually used."""
    
    def __init__(self):
        """Initialize ImportAnalyzer."""
        self.imports: Dict[str, ImportInfo] = {}  # Maps qualified names (or import_as) to ImportInfo
        self.used_names: Set[str] = set()         # Set of names actually used in the code
    
    def analyze_code(self, source_code: str) -> List[str]:
        """
        Analyze Python code and return a list of used imports (strings).
        
        Approach: parse AST, find import statements, then find which names or aliases
        are actually used. If any name from a module is used, mark the entire import as used.
        """
        tree = ast.parse(source_code)
        
        # First pass: collect all imports
        import_collector = ImportCollector()
        import_collector.visit(tree)
        self.imports.update(import_collector.imports)
        
        # Second pass: collect used names
        name_collector = NameCollector(self.imports)
        name_collector.visit(tree)
        self.used_names.update(name_collector.used_names)
        
        # Mark them used
        self._mark_used_imports()
        
        return self.get_used_import_statements()
    
    def _mark_used_imports(self):
        """
        If we find that a single name from a particular module is used,
        we mark *all* the imports from that same module as used.
        """
        # Step 1: gather modules that are used
        used_modules = set()
        
        # Check direct usage by name:
        for used_name in self.used_names:
            if used_name in self.imports:
                self.imports[used_name].is_used = True
                used_modules.add(self.imports[used_name].module_name)
            else:
                # Also check if it's in an alias_map or inside "names" of any import
                for info_key, info_val in self.imports.items():
                    if used_name in info_val.names or used_name in info_val.alias_map:
                        info_val.is_used = True
                        used_modules.add(info_val.module_name)
        
        # Step 2: now that we know which modules are used, mark all imports from those modules
        for info_val in self.imports.values():
            if info_val.module_name in used_modules:
                info_val.is_used = True

    def get_used_import_statements(self) -> List[str]:
        """
        Return the unique list of used import statements (no duplicates).
        """
        used_stmts = set()  # We'll collect unique statements here
        for info in self.imports.values():
            if info.is_used:
                used_stmts.add(info.import_statement)

        # Return as a sorted list or just list(used_stmts).
        return sorted(used_stmts)


class ImportCollector(ast.NodeVisitor):
    """
    Collects import statements into a dictionary: import_as => ImportInfo
    For example, "import os" => { 'os': ImportInfo(... module_name='os'...) }
    or from requests import get => { 'requests.get': ImportInfo(...) }
    """
    def __init__(self):
        self.imports: Dict[str, ImportInfo] = {}
    
    def visit_Import(self, node: ast.Import):
        for name in node.names:
            import_info = ImportInfo(
                import_statement=self._get_import_statement(node),
                module_name=name.name,
                names={name.asname or name.name}
            )
            
            if name.asname:
                import_info.alias_map[name.asname] = name.name
                
            self.imports[name.asname or name.name] = import_info
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        module_name = node.module or ''
        import_statement = self._get_import_statement(node)
        
        for name in node.names:
            qualified_name = f"{module_name}.{name.name}" if module_name else name.name
            import_info = ImportInfo(
                import_statement=import_statement,
                module_name=module_name,
                names={name.asname or name.name}
            )
            
            if name.asname:
                import_info.alias_map[name.asname] = name.name
                
            self.imports[qualified_name] = import_info
        
        self.generic_visit(node)

    def _get_import_statement(self, node: ast.AST) -> str:
        if isinstance(node, ast.Import):
            names = ', '.join(
                f"{alias.name} as {alias.asname}" if alias.asname else alias.name
                for alias in node.names
            )
            return f"import {names}"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            names = ', '.join(
                f"{alias.name} as {alias.asname}" if alias.asname else alias.name
                for alias in node.names
            )
            level = '.' * node.level
            return f"from {level}{module} import {names}"
        return ""


class NameCollector(ast.NodeVisitor):
    """
    Gathers all names that are used in the code (loaded).
    Then the ImportAnalyzer uses that info to decide which imports are needed.
    """
    def __init__(self, imports: Dict[str, ImportInfo]):
        super().__init__()
        self.imports = imports
        self.used_names: Set[str] = set()
    
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """
        For something like os.path.join, we parse backwards:
        node.attr = 'join', node.value.attr = 'path', node.value.value.id = 'os'
        We'll add 'os', 'os.path', and 'os.path.join' to used_names if that helps.
        """
        if isinstance(node.ctx, ast.Load):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                full_name = '.'.join(reversed(parts))  # e.g. "os.path.join"
                # We'll add the entire chain:
                self.used_names.add(full_name)
                # Also add the final base to handle partial usage:
                # e.g. 'os' if we used 'os.path'
                self.used_names.add(parts[-1])
        self.generic_visit(node)

