# tests/test_test_runner.py

"""
Tests for test_runner module.
"""
import unittest
from unittest.mock import patch, MagicMock

# Changed these lines to point to python_unittest_tool package:
from python_unittest_tool.test_runner import TestRunner, TestRunResult


class TestTestRunner(unittest.TestCase):
    """Test cases for TestRunner class."""
    
    def setUp(self):
        """Set up test cases."""
        self.runner = TestRunner()
    
    def test_init_default_test_dir(self):
        """Test default test directory initialization."""
        self.assertEqual(self.runner.test_dir, "tests")
    
    def test_init_custom_test_dir(self):
        """Test custom test directory initialization."""
        runner = TestRunner("custom_tests")
        self.assertEqual(runner.test_dir, "custom_tests")
    
    @patch('subprocess.run')
    def test_run_tests_successful(self, mock_run):
        """Test successful test execution."""
        # Mock successful subprocess execution
        mock_result = MagicMock(
            stdout="Test output",
            stderr="",
            returncode=0
        )
        mock_run.return_value = mock_result
        
        result = self.runner.run_tests()
        
        # Verify subprocess.run was called correctly
        mock_run.assert_called_once_with(
            ["python", "-m", "unittest", "discover", "tests"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Verify TestRunResult
        self.assertEqual(result.stdout, "Test output")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.has_failures)
    
    @patch('subprocess.run')
    def test_run_tests_with_failures(self, mock_run):
        """Test test execution with test failures."""
        # Mock failed tests
        mock_result = MagicMock(
            stdout="Test failures occurred",
            stderr="",
            returncode=1
        )
        mock_run.return_value = mock_result
        
        result = self.runner.run_tests()
        
        # Verify TestRunResult indicates failures
        self.assertEqual(result.stdout, "Test failures occurred")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.return_code, 1)
        self.assertTrue(result.has_failures)
    
    @patch('subprocess.run')
    def test_run_tests_subprocess_error(self, mock_run):
        """Test handling of subprocess execution errors."""
        import subprocess
        mock_run.side_effect = subprocess.SubprocessError("Command failed")
        
        with self.assertRaises(subprocess.SubprocessError) as context:
            self.runner.run_tests()
        
        self.assertIn("Failed to execute unittest discover", str(context.exception))


if __name__ == '__main__':
    unittest.main()
