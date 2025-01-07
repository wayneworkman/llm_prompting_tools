# python_unittest_tool/code_extractor.py

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

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if not self.class_stack:
            self.generic_visit(node)
            return
        # Extract lines
        start = node.lineno - 1
        end = node.end_lineno or node.lineno
        code_lines = ''.join(self.file_lines[start:end]).rstrip('\n')

        if node.name == self.test_name:
            self.class_name = self.class_stack[-1]
            self.test_code = code_lines
        elif node.name == 'setUp':
            if not self.class_name:
                self.class_name = self.class_stack[-1]
            self.setup_code = code_lines
        elif node.name == 'tearDown':
            if not self.class_name:
                self.class_name = self.class_stack[-1]
            self.teardown_code = code_lines

        self.generic_visit(node)

class CodeExtractor:
    def __init__(self):
        pass

    def extract_test_code(self, file_path: str, test_name: str) -> CodeSegment:
        try:
            file_lines = Path(file_path).read_text(encoding='utf-8').splitlines(keepends=True)
        except Exception:
            return CodeSegment(file_path, None, None, None, None, None, [])

        visitor = TestCodeVisitor(test_name, file_lines)
        source = ''.join(file_lines)
        try:
            tree = ast.parse(source)
            visitor.visit(tree)
        except Exception:
            return CodeSegment(file_path, None, None, None, None, None, [])

        return CodeSegment(
            file_path=file_path,
            class_name=visitor.class_name,
            setup_code=visitor.setup_code,
            teardown_code=visitor.teardown_code,
            test_code=visitor.test_code,
            source_code=None,
            imports=visitor.imports
        )

    def extract_source_code(self, file_path: str, function_name: str) -> CodeSegment:
        try:
            file_lines = Path(file_path).read_text(encoding='utf-8').splitlines(keepends=True)
        except Exception:
            return CodeSegment(file_path, None, None, None, None, None, [])

        visitor = SourceCodeVisitor(function_name, file_lines)
        source = ''.join(file_lines)
        try:
            tree = ast.parse(source)
            visitor.visit(tree)
        except Exception:
            return CodeSegment(file_path, None, None, None, None, None, [])

        return CodeSegment(
            file_path=file_path,
            class_name=visitor.class_name,
            setup_code=None,
            teardown_code=None,
            test_code=None,
            source_code=visitor.source_code,
            imports=visitor.imports
        )
