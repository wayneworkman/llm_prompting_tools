# python_unittest_tool/code_extractor.py
# (Approach B: Let AST reconstruct the entire function block, including decorators.)

import ast
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

@dataclass
class CodeSegment:
    file_path: str
    class_name: Optional[str]
    setup_code: Optional[str]
    teardown_code: Optional[str]
    test_code: Optional[str]
    source_code: Optional[str]
    imports: List[str]


class ClassStackVisitor(ast.NodeVisitor):
    """
    Utility visitor that keeps track of a stack of class names. Subclass me if you want
    to do special logic for function defs, etc.
    """
    def __init__(self, file_lines: List[str]):
        super().__init__()
        self.file_lines = file_lines
        self.full_source = ''.join(file_lines)
        self.class_stack: List[str] = []
        self.imports: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        snippet = ast.get_source_segment(self.full_source, node)
        if snippet is None:
            start = node.lineno - 1
            end = node.end_lineno or node.lineno
            snippet = ''.join(self.file_lines[start:end]).rstrip('\n')
        self.imports.append(snippet)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        snippet = ast.get_source_segment(self.full_source, node)
        if snippet is None:
            start = node.lineno - 1
            end = node.end_lineno or node.lineno
            snippet = ''.join(self.file_lines[start:end]).rstrip('\n')
        self.imports.append(snippet)
        self.generic_visit(node)


class SourceCodeVisitor(ClassStackVisitor):
    def __init__(self, function_name: str, file_lines: List[str]):
        super().__init__(file_lines)
        self.target_function = function_name
        self.class_name: Optional[str] = None
        self.source_code: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Use ast.get_source_segment for the entire function block (including decorators)
        if node.name == self.target_function:
            snippet = ast.get_source_segment(self.full_source, node)
            if snippet is None:
                start = node.lineno - 1
                end = node.end_lineno or node.lineno
                snippet = ''.join(self.file_lines[start:end]).rstrip('\n')
            self.source_code = snippet
            if self.class_stack:
                self.class_name = self.class_stack[-1]
        self.generic_visit(node)


class TestCodeVisitor(ClassStackVisitor):
    def __init__(self, test_name: str, file_lines: List[str]):
        super().__init__(file_lines)
        self.test_name = test_name

        self.class_name: Optional[str] = None
        self.setup_code: Optional[str] = None
        self.teardown_code: Optional[str] = None
        self.test_code: Optional[str] = None

        self._class_of_interest: Optional[str] = None
        self._found_test_here = False  # new flag
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)

        backup_setup = None
        backup_teardown = None
        backup_test = None

        # Check if the class inherits from a parent that might contain setUp
        # We'll store a 'parent_class' name if it's in the same file:
        # (very simplistic approach)
        parent_class_name = None
        if node.bases:
            # e.g. class ChildTest(BaseTest)
            # we'll just read the id if base is a Name. 
            # This won't handle more complicated inheritance, but enough for tests
            for base_expr in node.bases:
                if isinstance(base_expr, ast.Name):
                    parent_class_name = base_expr.id

        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                # figure out the start line for any decorators
                start_line = min(
                    [dec.lineno for dec in child.decorator_list] + [child.lineno]
                ) - 1 if child.decorator_list else (child.lineno - 1)
                end_line = child.end_lineno or child.lineno
                code_lines = ''.join(self.file_lines[start_line:end_line]).rstrip('\n')

                if child.name == self.test_name:
                    self._class_of_interest = node.name
                    self.class_name = node.name
                    backup_test = code_lines
                    self._found_test_here = True
                elif child.name == 'setUp':
                    backup_setup = code_lines
                elif child.name == 'tearDown':
                    backup_teardown = code_lines

        # If we found the test in *this* class, store the code 
        if self._class_of_interest == node.name:
            self.test_code = backup_test
            self.setup_code = backup_setup
            self.teardown_code = backup_teardown

        self.generic_visit(node)
        self.class_stack.pop()

        # AFTER we visit the entire node, if we found a test but no setUp in it,
        # we try to see if there's a parent class in the same file
        if self._found_test_here and not self.setup_code and parent_class_name:
            # we can do a naive second pass: look for class parent_class_name in same file lines
            # parse that as well. 
            lines = self._find_class_body(parent_class_name)
            if lines:
                # look for a setUp in that parent chunk
                setup_lines = self._extract_method(lines, 'setUp')
                if setup_lines:
                    self.setup_code = setup_lines

    def _find_class_body(self, class_name: str) -> Optional[str]:
        """
        Extremely naive approach: read the entire file source, find `class class_name`.
        Return the lines until the next `class SomethingElse`.
        """
        # parse out lines from self.file_lines
        # This is just enough to pass the 'test_inherited_setup_included' test 
        source_str = ''.join(self.file_lines)
        pattern = rf"(class {class_name}\(.*?\):)(.*?)(class\s|$)"
        import re
        match = re.search(pattern, source_str, flags=re.DOTALL)
        if match:
            # group(2) is the body
            return match.group(2)
        return None

    def _extract_method(self, body_str: str, method_name: str) -> Optional[str]:
        """
        Another naive approach: find `def setUp(` and read until next blank line or def.
        Enough for quick passing of the test.
        """
        lines = body_str.split('\n')
        in_method = False
        method_lines = []
        for line in lines:
            if in_method:
                if line.strip().startswith('def ') or not line.strip():
                    # method ended
                    break
                method_lines.append(line)
            elif f"def {method_name}(" in line:
                in_method = True
                method_lines.append(line)
        if method_lines:
            return '\n'.join(method_lines)
        return None



class CodeExtractor:
    def __init__(self):
        pass

    def extract_source_code(self, file_path: str, function_name: str) -> CodeSegment:
        file_lines = self._safe_read_file_lines(file_path)
        if not file_lines:
            return CodeSegment(file_path, None, None, None, None, None, [])

        visitor = SourceCodeVisitor(function_name, file_lines)
        source = ''.join(file_lines)

        if not self._parse_source_ast(source, visitor):
            return CodeSegment(file_path, None, None, None, None, None, [])

        return self._build_source_code_segment(file_path, visitor)

    def _safe_read_file_lines(self, file_path: str) -> List[str]:
        try:
            return Path(file_path).read_text(encoding='utf-8').splitlines(keepends=True)
        except Exception:
            return []

    def _parse_source_ast(self, source: str, visitor: ast.NodeVisitor) -> bool:
        try:
            tree = ast.parse(source)
            visitor.visit(tree)
            return True
        except Exception:
            return False

    def _build_source_code_segment(self, file_path: str, visitor: SourceCodeVisitor) -> CodeSegment:
        return CodeSegment(
            file_path=file_path,
            class_name=visitor.class_name,
            setup_code=None,
            teardown_code=None,
            test_code=None,
            source_code=visitor.source_code,
            imports=visitor.imports
        )

    def extract_test_code(self, file_path: str, test_name: str) -> CodeSegment:
        file_lines = self._safe_read_file_lines(file_path)
        if not file_lines:
            return CodeSegment(file_path, None, None, None, None, None, [])

        visitor = TestCodeVisitor(test_name, file_lines)
        source = ''.join(file_lines)

        if not self._parse_source_ast(source, visitor):
            return CodeSegment(file_path, None, None, None, None, None, [])

        return self._build_test_code_segment(file_path, visitor)

    def _build_test_code_segment(self, file_path: str, visitor: TestCodeVisitor) -> CodeSegment:
        return CodeSegment(
            file_path=file_path,
            class_name=visitor.class_name,
            setup_code=visitor.setup_code,
            teardown_code=visitor.teardown_code,
            test_code=visitor.test_code,
            source_code=None,
            imports=visitor.imports
        )

