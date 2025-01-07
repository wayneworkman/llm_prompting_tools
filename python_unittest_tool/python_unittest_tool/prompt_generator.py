# python_unittest_tool/prompt_generator.py

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
        if instructions:
            content.extend([
                "=== INSTRUCTIONS ===",
                instructions,
                ""  # Keep a blank line so indexing in tests remains consistent
            ])
        
        # Process each failure
        for i, failure in enumerate(failures, 1):
            content.extend([
                "=== TEST OUTPUT ===",
                failure.test_output,
                ""  # Again, a blank line after test output to keep sections aligned
            ])
            
            test_segment = failure.test_code
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
            
            # Add source code segments
            for segment in failure.source_segments:
                content.extend([
                    f"=== {segment.file_path} ===",
                    self._format_imports(segment.imports),
                    ""
                ])
                if segment.source_code:
                    content.append(segment.source_code)
                    content.append("")
            
            if i < len(failures):
                content.extend(["=" * 70, ""])
        
        self._write_output(content, output_file)
    
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
        
        # Strip leading/trailing spaces from each import line only;
        # do NOT sort them, to preserve the order from the extraction phase.
        cleaned = [imp.strip() for imp in imports]
        return "\n".join(cleaned)
    
    def _write_output(self, content: List[str], output_file: str) -> None:
        try:
            output_path = Path(output_file)
            output_path.write_text("\n".join(content), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to write prompt file: {e}")
            raise
