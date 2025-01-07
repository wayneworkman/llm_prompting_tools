# tests/test_test_parser.py

"""
Tests for test_parser module.
"""
import unittest

# Changed this line to point to python_unittest_tool package:
from python_unittest_tool.test_parser import TestOutputParser


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


    
    def test_failed_test_module_import_error(self):
        """
        Simulate an import error that yields a unittest.loader._FailedTest.
        Confirm that the parser sees it as an ERROR.
        """
        mock_output = """
======================================================================
ERROR: test_dependency_tracker (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_dependency_tracker
Traceback (most recent call last):
  File "/usr/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/path/to/python_unittest_tool/tests/test_dependency_tracker.py", line 9, in <module>
    from python_unittest_tool.dependency_tracker import DependencyTracker
ModuleNotFoundError: No module named 'python_unittest_tool.dependency_tracker'
======================================================================
"""
        failures = self.parser.parse_output(mock_output)
        self.assertEqual(len(failures), 1, "Should detect one failed test import.")
        failure = failures[0]
        self.assertEqual(failure.test_name, "test_dependency_tracker")
        self.assertEqual(failure.test_class, "_FailedTest")
        self.assertIn("ModuleNotFoundError", failure.failure_message)

        # Confirm we got the file path from the line, ignoring trailing text
        self.assertIn("test_dependency_tracker.py", failure.file_path)
        self.assertEqual(failure.line_number, 9)

    def test_failed_test_with_in_module_line(self):
        """
        Test a scenario where the line includes `, in <module>` after the line number.
        Ensures the new FILE_LINE_PATTERN captures it.
        """
        mock_output = """
======================================================================
ERROR: test_stuff (unittest.loader._FailedTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/some/path/file.py", line 10, in <module>
    from somepackage import something
ModuleNotFoundError: No module named 'somepackage'
======================================================================
"""
        failures = self.parser.parse_output(mock_output)
        self.assertEqual(len(failures), 1, "Should detect one error.")
        failure = failures[0]
        self.assertEqual(failure.test_name, "test_stuff")
        self.assertEqual(failure.test_class, "_FailedTest")
        self.assertIn("ModuleNotFoundError", failure.failure_message)
        self.assertIn("file.py", failure.file_path)
        self.assertEqual(failure.line_number, 10)



if __name__ == '__main__':
    unittest.main()
