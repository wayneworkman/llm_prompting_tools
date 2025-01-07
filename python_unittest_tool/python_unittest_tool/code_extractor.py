# python_unittest_tool/code_extractor.py
# (This file goes in the python_unittest_tool/ directory.)

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

        # Track the "class of interest" where the test is found
        self._class_of_interest: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        We'll parse the entire class. If it has the target test, we keep setUp/tearDown.
        Otherwise, we discard them.
        """
        self.class_stack.append(node.name)

        # Temporarily store setUp/tearDown/test code for THIS class
        backup_setup = None
        backup_teardown = None
        backup_test = None

        # We'll do a sub-visitor that collects these methods in the current class
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                start = child.lineno - 1
                end = child.end_lineno or child.lineno
                code_lines = ''.join(self.file_lines[start:end]).rstrip('\n')

                if child.name == self.test_name:
                    self._class_of_interest = node.name
                    self.class_name = node.name
                    backup_test = code_lines
                elif child.name == 'setUp':
                    backup_setup = code_lines
                elif child.name == 'tearDown':
                    backup_teardown = code_lines

        # Now if we found the test method in this class, store setUp/tearDown
        # (It's valid to store them even if they appear before the test in the code.)
        if self._class_of_interest == node.name:
            self.test_code = backup_test
            self.setup_code = backup_setup
            self.teardown_code = backup_teardown

        # Also gather imports by visiting child nodes
        self.generic_visit(node)
        self.class_stack.pop()


class CodeExtractor:
    def __init__(self):
        pass

    # ------------------
    # extract_source_code
    # ------------------
    def extract_source_code(self, file_path: str, function_name: str) -> CodeSegment:
        file_lines = self._safe_read_file_lines(file_path)
        if not file_lines:
            return CodeSegment(file_path, None, None, None, None, None, [])

        visitor = SourceCodeVisitor(function_name, file_lines)
        source = ''.join(file_lines)

        if not self._parse_source_ast(source, visitor):
            return CodeSegment(file_path, None, None, None, None, None, [])

        return self._build_source_code_segment(file_path, visitor)

    # Helper methods for extract_source_code
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

    # ----------------
    # extract_test_code
    # ----------------
    def extract_test_code(self, file_path: str, test_name: str) -> CodeSegment:
        file_lines = self._safe_read_file_lines(file_path)
        if not file_lines:
            return CodeSegment(file_path, None, None, None, None, None, [])

        visitor = TestCodeVisitor(test_name, file_lines)
        source = ''.join(file_lines)

        if not self._parse_source_ast(source, visitor):
            return CodeSegment(file_path, None, None, None, None, None, [])

        return self._build_test_code_segment(file_path, visitor)

    # Helper method for extract_test_code
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
