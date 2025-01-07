# tests/test_prompt_generator.py

"""
Tests for prompt_generator module.
"""
import unittest
from unittest.mock import patch
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
        
        # Check for new strings instead of === markers:
        self.assertIn("INSTRUCTIONS (from prompt_instructions.txt)", written_content, 
                    "Should include instructions heading in new format.")
        self.assertIn("Fix the failing test by implementing the correct behavior.", written_content)
        
        # Test Output is now labeled "Test Output" fenced by triple backticks
        self.assertIn("Test Output", written_content)
        self.assertIn("FAIL: test_function", written_content)  # part of the sample test_output

        # Check file path lines (instead of === /project/root/tests/test_module.py ===)
        self.assertIn("/project/root/tests/test_module.py", written_content)
        self.assertIn("/project/root/module.py", written_content)


    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_generate_prompt_without_instructions(self, mock_exists, mock_write_text):
        """Test generating prompt without instructions file."""
        mock_exists.return_value = False  # so no instructions
        
        # Generate prompt
        self.generator.generate_prompt([self.failure_info])
        
        written_content = mock_write_text.call_args[0][0]
        
        # Old test required:
        #   self.assertNotIn("=== INSTRUCTIONS ===", written_content)
        #   self.assertIn("=== TEST OUTPUT ===", written_content)
        #
        # Now we do:
        self.assertNotIn("INSTRUCTIONS (from prompt_instructions.txt)", written_content, 
                        "No instructions should appear if file doesn't exist.")
        self.assertIn("Test Output", written_content, 
                    "Should still have 'Test Output' even without instructions.")
        

    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_multiple_failures(self, mock_exists, mock_write_text):
        """Test generating prompt with multiple failures."""
        mock_exists.return_value = False
        
        # Create second failure (unchanged)
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
        
        written_content = mock_write_text.call_args[0][0]
        
        # Instead of searching for "=== TEST OUTPUT ===", we look for "Test Output"
        first_test_index = written_content.find("Test Output")
        second_test_index = written_content.find("Test Output", first_test_index + 1)
        
        # Confirm the second occurrence is after the first
        self.assertGreater(second_test_index, first_test_index, 
                        "Should have two 'Test Output' sections, one per failure.")
    

    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_import_formatting(self, mock_exists, mock_write_text):
        """
        Test formatting of import statements with usage-based filtering,
        but now with triple backticks instead of '=== ... ===' chunks.
        """
        mock_exists.return_value = False
        
        self.test_segment.imports = [
            "import sys",
            "from module import process_data",
            "import os",
            "from typing import List"
        ]
        self.test_segment.test_code = dedent('''
            def test_function(self):
                result = process_data("test")
                self.assertEqual(result, "TEST")
        ''').strip()
        self.failure_info.test_code = self.test_segment
        
        # Generate prompt
        self.generator.generate_prompt([self.failure_info])

        # Grab written content
        written_content = mock_write_text.call_args[0][0]

        # We'll find the lines after "/project/root/tests/test_module.py" in code fences
        # A simple approach: find that line, then find the "```python" that follows,
        # then read until the next triple backtick.
        
        lines = written_content.splitlines()
        try:
            start_idx = lines.index("/project/root/tests/test_module.py")
        except ValueError:
            self.fail("Could not find test_module.py heading in output")

        # The line after "test_module.py" should be "```python"
        # Then read until the closing "```"
        # e.g.:
        # /project/root/tests/test_module.py
        # ```python
        # from module import process_data
        # ...
        # ```
        if lines[start_idx + 1].strip() != "```python":
            self.fail("Did not find ```python fence where expected")

        code_fence_lines = []
        idx = start_idx + 2
        while idx < len(lines) and lines[idx].strip() != "```":
            code_fence_lines.append(lines[idx])
            idx += 1
        
        # Now parse out import lines
        import_lines = [
            ln for ln in code_fence_lines
            if ln.startswith("import ") or ln.startswith("from ")
        ]
        
        self.assertEqual(import_lines, ["from module import process_data"])


    
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
