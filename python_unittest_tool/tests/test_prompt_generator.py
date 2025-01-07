# tests/test_prompt_generator.py

"""
Tests for prompt_generator module.
"""
import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from textwrap import dedent

# Changed these lines to point to python_unittest_tool package:
from python_unittest_tool.prompt_generator import PromptGenerator, FailureInfo
from python_unittest_tool.code_extractor import CodeSegment


class TestPromptGenerator(unittest.TestCase):
    """Test cases for PromptGenerator class."""
    
    def setUp(self):
        """Set up test cases."""
        self.generator = PromptGenerator("/project/root")
        
        # Sample code segments
        self.test_segment = CodeSegment(
            file_path="/project/root/tests/test_module.py",
            class_name="TestClass",
            setup_code=dedent('''
                def setUp(self):
                    self.data = "test"
            ''').strip(),
            teardown_code=dedent('''
                def tearDown(self):
                    self.data = None
            ''').strip(),
            test_code=dedent('''
                def test_function(self):
                    self.assertEqual(process_data(self.data), "TEST")
            ''').strip(),
            source_code=None,
            imports=["import unittest", "from module import process_data"]
        )
        
        self.source_segment = CodeSegment(
            file_path="/project/root/module.py",
            class_name=None,
            setup_code=None,
            teardown_code=None,
            test_code=None,
            source_code=dedent('''
                def process_data(data: str) -> str:
                    return data.upper()
            ''').strip(),
            imports=["from typing import Optional"]
        )
        
        # Sample failure info
        self.failure_info = FailureInfo(
            test_output=dedent('''
                ======================================================================
                FAIL: test_function (tests.test_module.TestClass)
                ----------------------------------------------------------------------
                Traceback (most recent call last):
                  File "/project/root/tests/test_module.py", line 12, in test_function
                    self.assertEqual(process_data(self.data), "TEST")
                AssertionError: 'test' != 'TEST'
            ''').strip(),
            test_code=self.test_segment,
            source_segments=[self.source_segment]
        )
    
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_generate_prompt_with_instructions(self, mock_read_text, mock_exists, mock_write_text):
        """Test generating prompt with instructions file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_read_text.return_value = "Fix the failing test by implementing the correct behavior."
        
        # Generate prompt
        self.generator.generate_prompt([self.failure_info])
        
        # Get the written content
        written_content = mock_write_text.call_args[0][0]
        
        # Verify content structure
        self.assertIn("=== INSTRUCTIONS ===", written_content)
        self.assertIn("Fix the failing test", written_content)
        self.assertIn("=== TEST OUTPUT ===", written_content)
        self.assertIn("FAIL: test_function", written_content)
        self.assertIn("=== /project/root/tests/test_module.py ===", written_content)
        self.assertIn("=== /project/root/module.py ===", written_content)
    
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_generate_prompt_without_instructions(self, mock_exists, mock_write_text):
        """Test generating prompt without instructions file."""
        # Setup mock
        mock_exists.return_value = False
        
        # Generate prompt
        self.generator.generate_prompt([self.failure_info])
        
        # Get the written content
        written_content = mock_write_text.call_args[0][0]
        
        # Verify content structure
        self.assertNotIn("=== INSTRUCTIONS ===", written_content)
        self.assertIn("=== TEST OUTPUT ===", written_content)
    
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_multiple_failures(self, mock_exists, mock_write_text):
        """Test generating prompt with multiple failures."""
        # Setup mock
        mock_exists.return_value = False
        
        # Create second failure
        second_failure = FailureInfo(
            test_output="FAIL: test_another",
            test_code=CodeSegment(
                file_path="/project/root/tests/test_module.py",
                class_name="TestClass",
                setup_code=None,
                teardown_code=None,
                test_code="def test_another(self):\n    self.assertTrue(False)",
                source_code=None,
                imports=[]
            ),
            source_segments=[]
        )
        
        # Generate prompt
        self.generator.generate_prompt([self.failure_info, second_failure])
        
        # Get the written content
        written_content = mock_write_text.call_args[0][0]
        
        # Verify content structure
        self.assertIn("=" * 70, written_content)  # Separator between failures
        first_test_index = written_content.find("=== TEST OUTPUT ===")
        second_test_index = written_content.find("=== TEST OUTPUT ===", first_test_index + 1)
        self.assertGreater(second_test_index, first_test_index)
    
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_import_formatting(self, mock_exists, mock_write_text):
        """Test formatting of import statements."""
        # Setup mock
        mock_exists.return_value = False
        
        # Add more imports in random order
        self.test_segment.imports = [
            "import sys",
            "from module import process_data",
            "import os",
            "from typing import List"
        ]
        
        # Generate prompt
        self.generator.generate_prompt([self.failure_info])
        
        # Get the written content
        written_content = mock_write_text.call_args[0][0]
        
        # Verify imports are sorted
        import_section = written_content.split("===")[2]  # Get the test file section
        import_lines = [line for line in import_section.split("\n") if line.startswith(("import", "from"))]
        self.assertEqual(import_lines, sorted(self.test_segment.imports))
    
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_empty_failure_list(self, mock_exists, mock_write_text):
        """Test generating prompt with no failures."""
        # Setup mock
        mock_exists.return_value = False
        
        # Generate prompt
        self.generator.generate_prompt([])
        
        # Get the written content
        written_content = mock_write_text.call_args[0][0]
        
        # Verify content is minimal
        self.assertEqual(written_content.strip(), "")
    
    @patch('pathlib.Path.write_text')
    def test_write_error_handling(self, mock_write_text):
        """Test error handling when writing fails."""
        # Setup mock to raise an error
        mock_write_text.side_effect = IOError("Write failed")
        
        # Verify error is raised
        with self.assertRaises(IOError):
            self.generator.generate_prompt([self.failure_info])


if __name__ == '__main__':
    unittest.main()
