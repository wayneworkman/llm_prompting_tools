# tests/test_code_extractor.py
# (Place this file in the tests/ directory, replacing the original.)

"""
Tests for code_extractor module.
"""
import unittest
from textwrap import dedent
from pathlib import Path
from unittest.mock import patch

# Changed this line to point to python_unittest_tool package:
from python_unittest_tool.code_extractor import CodeExtractor, CodeSegment


class TestCodeExtractor(unittest.TestCase):
    """Test cases for CodeExtractor class."""
    
    def setUp(self):
        """Set up test cases."""
        self.extractor = CodeExtractor()
        
        # Remove .lstrip() so class is truly at column 0
        self.mock_test_file = dedent('''
            import unittest
            from module import function_under_test

            class TestClass(unittest.TestCase):
                def setUp(self):
                    self.data = "test data"

                def tearDown(self):
                    self.data = None

                def test_something(self):
                    """Test something."""
                    result = function_under_test(self.data)
                    self.assertTrue(result)
        ''')
        
        self.mock_source_file = dedent('''
            from typing import Optional

            class MyClass:
                def function_under_test(self, data: str) -> bool:
                    """Test function."""
                    return bool(data)
        ''')

    @patch('pathlib.Path.read_text')
    def test_extract_test_code(self, mock_read_text):
        """Test extracting test code."""
        mock_read_text.return_value = self.mock_test_file
        
        result = self.extractor.extract_test_code('test_file.py', 'test_something')
        
        self.assertEqual(result.file_path, 'test_file.py')
        self.assertEqual(result.class_name, 'TestClass')
        self.assertIn('def setUp(self):', result.setup_code)
        self.assertIn('def tearDown(self):', result.teardown_code)
        self.assertIn('def test_something(self):', result.test_code)
        self.assertEqual(len(result.imports), 2)
    
    @patch('pathlib.Path.read_text')
    def test_extract_source_code(self, mock_read_text):
        """Test extracting source code."""
        mock_read_text.return_value = self.mock_source_file
        
        result = self.extractor.extract_source_code('source_file.py', 'function_under_test')
        
        self.assertEqual(result.file_path, 'source_file.py')
        self.assertEqual(result.class_name, 'MyClass')
        self.assertIn('def function_under_test(self, data: str)', result.source_code)
        self.assertEqual(len(result.imports), 1)
    
    @patch('pathlib.Path.read_text')
    def test_extract_nonexistent_test(self, mock_read_text):
        """Test extracting non-existent test code."""
        mock_read_text.return_value = self.mock_test_file
        
        result = self.extractor.extract_test_code('test_file.py', 'nonexistent_test')
        
        self.assertIsNone(result.test_code)
        self.assertIsNone(result.class_name)
    
    @patch('pathlib.Path.read_text')
    def test_extract_nonexistent_source(self, mock_read_text):
        """Test extracting non-existent source code."""
        mock_read_text.return_value = self.mock_source_file
        
        result = self.extractor.extract_source_code('source_file.py', 'nonexistent_function')
        
        self.assertIsNone(result.source_code)
        self.assertIsNone(result.class_name)


if __name__ == '__main__':
    unittest.main()
