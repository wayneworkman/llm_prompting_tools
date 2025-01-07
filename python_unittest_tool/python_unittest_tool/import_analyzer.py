"""
Module for analyzing and extracting used imports from Python code.
"""
import ast
from dataclasses import dataclass, field
from typing import Set, Dict, List, Optional
from pathlib import Path


@dataclass
class ImportInfo:
    """Container for import information."""
    import_statement: str  # The original import statement
    module_name: str      # The module being imported
    names: Set[str]      # Names being imported
    is_used: bool = False
    alias_map: Dict[str, str] = field(default_factory=dict)  # Maps aliases to original names


class ImportAnalyzer:
    """Analyzes Python code to determine which imports are actually used."""
    
    def __init__(self):
        """Initialize ImportAnalyzer."""
        self.imports: Dict[str, ImportInfo] = {}  # Maps qualified names to ImportInfo
        self.used_names: Set[str] = set()        # Set of names actually used in the code
        self._current_module = None
    
    def analyze_code(self, source_code: str) -> List[str]:
        """
        Analyze Python code and return list of used imports.
        
        Args:
            source_code: Python source code to analyze
            
        Returns:
            List of import statements that are actually used
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
        
        # Determine which imports are used
        self._mark_used_imports()
        
        return self.get_used_import_statements()
    
    def _mark_used_imports(self):
        """Mark imports as used based on collected used names."""
        for name in self.used_names:
            # Check direct imports
            if name in self.imports:
                self.imports[name].is_used = True
                continue
                
            # Check imported names
            for import_info in self.imports.values():
                if name in import_info.names:
                    import_info.is_used = True
                    continue
                    
                # Check aliases
                if name in import_info.alias_map:
                    import_info.is_used = True
                    continue
    
    def get_used_import_statements(self) -> List[str]:
        """
        Get list of import statements that are actually used.
        
        Returns:
            List of import statements
        """
        return [
            info.import_statement
            for info in self.imports.values()
            if info.is_used
        ]


class ImportCollector(ast.NodeVisitor):
    """AST visitor that collects import information."""
    
    def __init__(self):
        """Initialize ImportCollector."""
        self.imports: Dict[str, ImportInfo] = {}
    
    def visit_Import(self, node: ast.Import):
        """Visit Import node."""
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
        """Visit ImportFrom node."""
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
        """Get the original import statement from an AST node."""
        if isinstance(node, ast.Import):
            names = ', '.join(
                f"{name.name} as {name.asname}" if name.asname else name.name
                for name in node.names
            )
            return f"import {names}"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            names = ', '.join(
                f"{name.name} as {name.asname}" if name.asname else name.name
                for name in node.names
            )
            level = '.' * node.level
            return f"from {level}{module} import {names}"
        return ""


class NameCollector(ast.NodeVisitor):
    """AST visitor that collects used names."""
    
    def __init__(self, imports: Dict[str, ImportInfo]):
        """
        Initialize NameCollector.
        
        Args:
            imports: Dictionary of import information
        """
        self.imports = imports
        self.used_names: Set[str] = set()
    
    def visit_Name(self, node: ast.Name):
        """Visit Name node."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Visit Attribute node."""
        if isinstance(node.ctx, ast.Load):
            # Handle cases like module.function
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                # Build full name from right to left
                full_name = '.'.join(reversed(parts))
                self.used_names.add(full_name)
                # Also add the root name
                self.used_names.add(parts[-1])
        self.generic_visit(node)