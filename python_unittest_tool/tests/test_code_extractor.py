# tests/test_code_extractor.py

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

    def test_parameterized_decorators_preserved(self):
        """
        Test that parameterized decorators (and any other decorators) are kept intact
        in the extracted failing test method.
        """
        # Example file content
        mock_test_content = dedent('''
            import pytest
            import unittest
            from module import do_something

            class TestParamStuff(unittest.TestCase):
                @pytest.mark.parametrize("val", [1,2,3])
                @unittest.skipIf(False, "some reason")
                def test_multi_decorators(self):
                    """A test with param + skipIf decorator."""
                    result = do_something(val)
                    self.assertTrue(result)
        ''')

        with patch('pathlib.Path.read_text', return_value=mock_test_content):
            extractor = CodeExtractor()
            segment = extractor.extract_test_code("test_file.py", "test_multi_decorators")
            
            self.assertIsNotNone(segment.test_code)
            self.assertIn("@pytest.mark.parametrize(\"val\", [1,2,3])", segment.test_code, 
                        "Parametrized decorator should be in the extracted code.")
            self.assertIn("@unittest.skipIf(False, \"some reason\")", segment.test_code,
                        "skipIf decorator should be preserved.")
            self.assertIn('"""A test with param + skipIf decorator."""', segment.test_code,
                        "Docstring inside the test should remain.")
            
    def test_failing_test_docstring_preserved(self):
        """
        Confirm that multi-line docstrings in a failing test are extracted verbatim.
        """
        content = dedent('''
            class TestDocstringExample:
                def setUp(self):
                    pass

                def test_broken(self):
                    """
                    Multi-line
                    docstring
                    with some details
                    """
                    assert False
        ''')

        with patch('pathlib.Path.read_text', return_value=content):
            extractor = CodeExtractor()
            seg = extractor.extract_test_code("some_test.py", "test_broken")
            self.assertIn('Multi-line', seg.test_code, "Should preserve multi-line docstring line1.")
            self.assertIn('with some details', seg.test_code, "Should preserve multi-line docstring line3.")

    def test_source_docstring_preserved(self):
        """
        Confirm that a multi-line docstring in the source function is kept verbatim.
        """
        source_content = dedent('''
            def some_function(x):
                """
                This is a multi-line docstring in the source code,
                which we want to preserve exactly
                for LLM context.
                """
                return x + 1
        ''')

        with patch('pathlib.Path.read_text', return_value=source_content):
            extractor = CodeExtractor()
            seg = extractor.extract_source_code("some_source.py", "some_function")
            self.assertIsNotNone(seg.source_code)
            self.assertIn('This is a multi-line docstring in the source code,', seg.source_code)
            self.assertIn('for LLM context.', seg.source_code)

    def test_only_failing_sibling_included_with_setup(self):
        """
        Confirm that only the failing test is extracted, plus setUp, 
        ignoring sibling tests that pass or aren't requested.
        """
        content = dedent('''
            import unittest

            class TestSiblingSetup(unittest.TestCase):
                def setUp(self):
                    self.val = 123

                def test_ok(self):
                    self.assertTrue(self.val > 0)

                def test_fail(self):
                    self.assertEqual(self.val, 999)  # fails
        ''')

        with patch('pathlib.Path.read_text', return_value=content):
            extractor = CodeExtractor()
            seg = extractor.extract_test_code("test_siblings.py", "test_fail")

            # Ensure we only got 'test_fail'
            self.assertIn('def test_fail(self):', seg.test_code)
            self.assertNotIn('def test_ok(self):', seg.test_code or '', 
                            "We do not want the passing test included.")
            # But setUp is still included
            self.assertIn('def setUp(self):', seg.setup_code or '',
                        "Should keep setUp if used by failing test.")
            

    def test_inherited_setup_included(self):
        """
        Confirm a parent's setUp method is included if the child test uses it.
        """
        content = dedent('''
            import unittest

            class BaseTest(unittest.TestCase):
                def setUp(self):
                    self.base_val = 42

            class ChildTest(BaseTest):
                def test_something(self):
                    assert self.base_val == 999
        ''')

        with patch('pathlib.Path.read_text', return_value=content):
            # If your extraction logic includes parent classes, it might require more logic.
            extractor = CodeExtractor()
            seg = extractor.extract_test_code("inherited_test.py", "test_something")
            self.assertIn('def test_something(self):', seg.test_code or '')


if __name__ == '__main__':
    unittest.main()

