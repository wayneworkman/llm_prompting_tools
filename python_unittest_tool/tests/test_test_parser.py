# tests/test_test_parser.py

"""
Tests for test_parser module.
"""
import unittest

# Changed this line to point to python_unittest_tool package:
from python_unittest_tool.test_parser import TestOutputParser, TestFailure


class TestTestOutputParser(unittest.TestCase):
    """Test cases for TestOutputParser class."""
    
    def setUp(self):
        """Set up test cases."""
        self.parser = TestOutputParser()
        self.sample_failure = '''
======================================================================
FAIL: test_directory_pattern_with_subdirs (test_gitignore_utils.TestGitignoreUtils)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/user/project/tests/test_gitignore_utils.py", line 99, in test_directory_pattern_with_subdirs
    self.assertFalse(should_include_file(os.path.join(self.root, "subdir"), self.root, gitignore_spec))
AssertionError: True is not false
'''
        self.sample_multiple_failures = self.sample_failure + '''
======================================================================
FAIL: test_should_include_file (test_gitignore_utils.TestGitignoreUtils)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/user/project/tests/test_gitignore_utils.py", line 56, in test_should_include_file
    self.assertFalse(should_include_file(os.path.join(self.root, "excluded_dir"), self.root, gitignore_spec))
AssertionError: True is not false
'''

    def test_parse_single_failure(self):
        """Test parsing a single test failure."""
        failures = self.parser.parse_output(self.sample_failure)
        
        self.assertEqual(len(failures), 1)
        failure = failures[0]
        
        self.assertEqual(failure.test_name, "test_directory_pattern_with_subdirs")
        self.assertEqual(failure.test_class, "TestGitignoreUtils")
        self.assertEqual(failure.file_path, "/home/user/project/tests/test_gitignore_utils.py")
        self.assertEqual(failure.line_number, 99)
        self.assertEqual(failure.failure_message, "AssertionError: True is not false")
        self.assertIn("Traceback (most recent call last):", failure.traceback)
        self.assertIn(failure.failure_message, failure.full_output)
    
    def test_parse_multiple_failures(self):
        """Test parsing multiple test failures."""
        failures = self.parser.parse_output(self.sample_multiple_failures)
        
        self.assertEqual(len(failures), 2)
        self.assertEqual(failures[0].test_name, "test_directory_pattern_with_subdirs")
        self.assertEqual(failures[1].test_name, "test_should_include_file")
    
    def test_number_of_issues_limit(self):
        """Test limiting the number of failures parsed."""
        parser = TestOutputParser(number_of_issues=1)
        failures = parser.parse_output(self.sample_multiple_failures)
        
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].test_name, "test_directory_pattern_with_subdirs")
    
    def test_parse_empty_output(self):
        """Test parsing empty output."""
        failures = self.parser.parse_output("")
        self.assertEqual(len(failures), 0)
    
    def test_parse_invalid_output(self):
        """Test parsing invalid output format."""
        failures = self.parser.parse_output("Some random output without proper format")
        self.assertEqual(len(failures), 0)
    
    def test_parse_error_output(self):
        """Test parsing ERROR instead of FAIL."""
        error_output = self.sample_failure.replace("FAIL:", "ERROR:")
        failures = self.parser.parse_output(error_output)
        
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].test_name, "test_directory_pattern_with_subdirs")


if __name__ == '__main__':
    unittest.main()
