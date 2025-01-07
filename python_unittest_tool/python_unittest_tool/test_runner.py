"""
Module for executing unittest discover and capturing its output.
"""
import subprocess
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class TestRunResult:
    """Container for test run results."""
    stdout: str
    stderr: str
    return_code: int
    
    @property
    def has_failures(self) -> bool:
        """Returns True if the test run had failures or errors."""
        return self.return_code != 0


class TestRunner:
    """Handles execution of unittest discover command and captures output."""
    
    def __init__(self, test_dir: str = "tests"):
        """
        Initialize TestRunner.
        
        Args:
            test_dir: Directory containing test files. Defaults to "tests".
        """
        self.test_dir = test_dir
    
    def run_tests(self) -> TestRunResult:
        """
        Execute unittest discover and capture output.
        
        Returns:
            TestRunResult containing stdout, stderr, and return code
        
        Raises:
            subprocess.SubprocessError: If the subprocess execution fails
        """
        try:
            # Using subprocess.run with text=True to get string output
            result = subprocess.run(
                ["python", "-m", "unittest", "discover", self.test_dir],
                capture_output=True,
                text=True,
                check=False  # Don't raise on test failures
            )
            
            return TestRunResult(
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode
            )
            
        except subprocess.SubprocessError as e:
            # Re-raise with more context
            raise subprocess.SubprocessError(
                f"Failed to execute unittest discover in {self.test_dir}: {str(e)}"
            ) from e