"""
Module for parsing unittest output and extracting failure information.
"""
from dataclasses import dataclass
from typing import List, Optional
import re
from pathlib import Path


@dataclass
class TestFailure:
    """Container for information about a single test failure."""
    test_name: str
    test_class: str
    file_path: str
    line_number: int
    failure_message: str
    traceback: str
    full_output: str  # The complete output block for this failure


class TestOutputParser:
    """Parses unittest output to extract test failures."""

    # Regular expressions for parsing unittest output
    FAILURE_PATTERN = re.compile(
        r"^(FAIL|ERROR): (test_\w+) \(([\w.]+)\)",
        re.MULTILINE
    )
    # Updated to handle trailing text like `, in <module>`:
    FILE_LINE_PATTERN = re.compile(
        r'File "([^"]+)", line (\d+)(?:, .*)?',
        re.MULTILINE
    )

    def __init__(self, number_of_issues: int = 0):
        """
        Initialize TestOutputParser.

        Args:
            number_of_issues: Number of issues to extract (0 means all)
        """
        self.number_of_issues = number_of_issues

    def parse_output(self, test_output: str) -> List[TestFailure]:
        """
        Parse unittest output and extract test failures.

        Args:
            test_output: Complete unittest output string

        Returns:
            List of TestFailure objects
        """
        failures = []

        # Split output into individual failure blocks
        failure_blocks = self._split_into_failure_blocks(test_output)

        # Process each failure block
        for block in failure_blocks:
            failure = self._parse_failure_block(block)
            if failure:
                failures.append(failure)
                if self.number_of_issues > 0 and len(failures) >= self.number_of_issues:
                    break

        return failures

    def _split_into_failure_blocks(self, output: str) -> List[str]:
        """
        Split the unittest output into individual failure blocks.

        Args:
            output: Complete unittest output

        Returns:
            List of failure block strings
        """
        # We split on lines of "====..."
        blocks = re.split(r'(?m)^=+$', output)
        return [block.strip() for block in blocks if block.strip()]

    def _parse_failure_block(self, block: str) -> Optional[TestFailure]:
        """
        Parse a single failure block into a TestFailure object.

        Args:
            block: Single failure block string

        Returns:
            TestFailure object or None if parsing fails
        """
        # 1) Identify a 'FAIL' or 'ERROR' line
        header_match = self.FAILURE_PATTERN.search(block)
        if not header_match:
            return None

        test_name = header_match.group(2)
        test_class_path = header_match.group(3)
        test_class = test_class_path.split('.')[-1]

        # 2) Grab the **last** file line match in the traceback
        file_matches = list(self.FILE_LINE_PATTERN.finditer(block))
        if not file_matches:
            return None
        file_match = file_matches[-1]  # use the last match

        file_path = file_match.group(1)
        line_number = int(file_match.group(2))

        # 3) The final line in the block is typically the AssertionError or module error
        lines = block.strip().split('\n')
        failure_message = lines[-1].strip()

        # 4) Extract the traceback portion
        header_end = block.find('Traceback')
        if header_end == -1:
            header_end = 0
        traceback = block[header_end:block.rfind('\n')].strip()

        return TestFailure(
            test_name=test_name,
            test_class=test_class,
            file_path=file_path,
            line_number=line_number,
            failure_message=failure_message,
            traceback=traceback,
            full_output=block.strip()
        )
