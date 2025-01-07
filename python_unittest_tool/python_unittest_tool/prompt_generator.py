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
        """
        Generate a prompt file that includes optional instructions, test output,
        and relevant code segments from both the failing tests and source files.
        """
        content = []

        instructions = self._read_instructions()
        self._maybe_add_instructions(content, instructions)

        # Loop through each failure
        for i, failure in enumerate(failures, 1):
            self._add_failure_section(content, failure)
            # Optionally add a separator between failures, if you want
            if i < len(failures):
                content.append("")  # blank line

        self._write_output(content, output_file)

    def _maybe_add_instructions(self, content: List[str], instructions: Optional[str]) -> None:
        """
        If we have a 'prompt_instructions.txt', insert it before everything else.
        """
        if instructions:
            # We’ll also fence this with triple backticks, though you could do differently.
            content.append("INSTRUCTIONS (from prompt_instructions.txt)")
            content.append("```")
            content.append(instructions)
            content.append("```")
            content.append("")  # blank line

    def _add_failure_section(self, content: List[str], failure: FailureInfo) -> None:
        """
        Add a block for each test failure, including its test output and code.
        """
        # Test output (fenced)
        content.append("Test Output")
        content.append("```")
        content.append(failure.test_output.strip())
        content.append("```")
        content.append("")  # blank line

        # Test code (wrapped in triple backticks)
        self._add_test_segment(content, failure.test_code)

        # Source segments
        self._add_source_segments(content, failure.source_segments)

    def _add_test_segment(self, content: List[str], test_segment: CodeSegment) -> None:
        """
        Add the failing test code (imports, setup, teardown, test function),
        using triple-backtick fences
        """
        # Usage-based import filtering
        if test_segment.test_code and test_segment.imports:
            from python_unittest_tool.import_analyzer import ImportAnalyzer
            analyzer = ImportAnalyzer()
            combined_source = "\n".join(test_segment.imports) + "\n" + test_segment.test_code
            used_imports = analyzer.analyze_code(combined_source)
            test_segment.imports = used_imports

        # Output the file path, followed by code fences
        content.append(test_segment.file_path)
        content.append("```python")

        # Show imports
        for imp in test_segment.imports:
            content.append(imp.strip())

        content.append("")  # blank line

        if test_segment.setup_code:
            content.append(test_segment.setup_code.strip())
            content.append("")  # blank line

        if test_segment.teardown_code:
            content.append(test_segment.teardown_code.strip())
            content.append("")  # blank line

        if test_segment.test_code:
            content.append(test_segment.test_code.strip())

        content.append("```")
        content.append("")  # blank line

    def _add_source_segments(self, content: List[str], source_segments: List[CodeSegment]) -> None:
        """
        Add the relevant source code in triple-backtick fences.
        """
        for segment in source_segments:
            # Filter imports
            if segment.source_code and segment.imports:
                from python_unittest_tool.import_analyzer import ImportAnalyzer
                analyzer = ImportAnalyzer()
                combined_source = "\n".join(segment.imports) + "\n" + segment.source_code
                used_imports = analyzer.analyze_code(combined_source)
                segment.imports = used_imports

            # file path
            content.append(segment.file_path)
            content.append("```python")

            # import lines
            for imp in segment.imports:
                content.append(imp.strip())
            content.append("")  # blank line

            # actual source code
            if segment.source_code:
                content.append(segment.source_code.strip())

            content.append("```")
            content.append("")  # blank line

    def _read_instructions(self) -> Optional[str]:
        """
        If prompt_instructions.txt is present, read it; otherwise return None.
        """
        instructions_file = self.project_root / "prompt_instructions.txt"
        try:
            if instructions_file.exists():
                return instructions_file.read_text(encoding='utf-8').strip()
            return None
        except Exception as e:
            logger.warning(f"Failed to read prompt_instructions.txt: {e}")
            return None
    
    def _write_output(self, content: List[str], output_file: str) -> None:
        """
        Write the final prompt to disk.
        """
        try:
            output_path = Path(output_file)
            # Join with newlines
            output_text = "\n".join(content).rstrip() + "\n"
            output_path.write_text(output_text, encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to write prompt file: {e}")
            raise
