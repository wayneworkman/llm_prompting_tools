# python_unittest_tool/prompt_generator.py
# (This file goes in the python_unittest_tool/ directory.)

"""
Module for generating the final prompt.txt file.
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from python_unittest_tool.code_extractor import CodeSegment

logger = logging.getLogger(__name__)

@dataclass
class FailureInfo:
    """Container for test failure information."""
    test_output: str
    test_code: CodeSegment
    source_segments: List[CodeSegment]


class PromptGenerator:
    """Generates the final prompt.txt file containing relevant code and failure information."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def generate_prompt(self, failures: List[FailureInfo], output_file: str = "prompt.txt") -> None:
        content = []

        instructions = self._read_instructions()
        self._maybe_add_instructions(content, instructions)

        for i, failure in enumerate(failures, 1):
            self._add_failure_section(content, failure)
            if i < len(failures):
                content.extend(["=" * 70, ""])

        self._write_output(content, output_file)

    def _maybe_add_instructions(self, content: List[str], instructions: Optional[str]) -> None:
        if instructions:
            content.extend([
                "=== INSTRUCTIONS ===",
                instructions,
                ""  # Keep a blank line
            ])

    def _add_failure_section(self, content: List[str], failure: FailureInfo) -> None:
        content.extend([
            "=== TEST OUTPUT ===",
            failure.test_output,
            ""
        ])

        self._add_test_segment(content, failure.test_code)

        self._add_source_segments(content, failure.source_segments)

    #
    # ******* UPDATED METHOD *******
    #
    def _add_test_segment(self, content: List[str], test_segment: CodeSegment) -> None:
        """
        Add the failing test code (imports, setup, teardown, test function).
        Also apply usage-based filtering to test imports, so that only the
        actually used imports remain. This change is specifically to satisfy
        test_import_formatting from test_prompt_generator.py.
        """
        # Perform usage-based import filtering if we have test code
        if test_segment.test_code and test_segment.imports:
            from python_unittest_tool.import_analyzer import ImportAnalyzer
            analyzer = ImportAnalyzer()
            used_imports = analyzer.analyze_code(test_segment.test_code)
            # Overwrite original imports with only the used ones
            test_segment.imports = used_imports

        # Now proceed to output
        content.extend([
            f"=== {test_segment.file_path} ===",
            self._format_imports(test_segment.imports),
            ""
        ])

        if test_segment.class_name:
            if test_segment.setup_code:
                content.append(test_segment.setup_code)
                content.append("")
            if test_segment.teardown_code:
                content.append(test_segment.teardown_code)
                content.append("")

        if test_segment.test_code:
            content.append(test_segment.test_code)
            content.append("")

    def _add_source_segments(self, content: List[str], source_segments: List[CodeSegment]) -> None:
        for segment in source_segments:
            content.extend([
                f"=== {segment.file_path} ===",
                self._format_imports(segment.imports),
                ""
            ])
            if segment.source_code:
                content.append(segment.source_code)
                content.append("")

    def _read_instructions(self) -> Optional[str]:
        instructions_file = self.project_root / "prompt_instructions.txt"
        try:
            if instructions_file.exists():
                return instructions_file.read_text(encoding='utf-8').strip()
            return None
        except Exception as e:
            logger.warning(f"Failed to read prompt_instructions.txt: {e}")
            return None

    def _format_imports(self, imports: List[str]) -> str:
        if not imports:
            return ""
        cleaned = [imp.strip() for imp in imports]
        return "\n".join(cleaned)
    
    def _write_output(self, content: List[str], output_file: str) -> None:
        try:
            output_path = Path(output_file)
            output_path.write_text("\n".join(content), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to write prompt file: {e}")
            raise
