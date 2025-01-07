# tests/test_import_analyzer.py

"""
Tests for import_analyzer module.
"""
import unittest
from textwrap import dedent

# Changed this line to point to python_unittest_tool package:
from python_unittest_tool.import_analyzer import ImportAnalyzer, ImportInfo


class TestImportAnalyzer(unittest.TestCase):
    """Test cases for ImportAnalyzer class."""
    
    def setUp(self):
        """Set up test cases."""
        self.analyzer = ImportAnalyzer()
    
    def test_simple_import(self):
        """Test analyzing simple import statement."""
        code = dedent('''
            import os
            
            def test_function():
                path = os.path.join('a', 'b')
        ''')
        
        used_imports = self.analyzer.analyze_code(code)
        self.assertEqual(len(used_imports), 1)
        self.assertIn('import os', used_imports)
    
    def test_unused_import(self):
        """Test handling unused imports."""
        code = dedent('''
            import os
            import sys
            
            def test_function():
                path = os.path.join('a', 'b')
        ''')
        
        used_imports = self.analyzer.analyze_code(code)
        self.assertEqual(len(used_imports), 1)
        self.assertIn('import os', used_imports)
        self.assertNotIn('import sys', used_imports)
    
    def test_import_from(self):
        """Test handling 'import from' statements."""
        code = dedent('''
            from os.path import join, dirname
            
            def test_function():
                path = join('a', 'b')
        ''')
        
        used_imports = self.analyzer.analyze_code(code)
        self.assertEqual(len(used_imports), 1)
        self.assertIn('from os.path import join, dirname', used_imports)
    
    def test_import_alias(self):
        """Test handling import aliases."""
        code = dedent('''
            import os.path as osp
            
            def test_function():
                path = osp.join('a', 'b')
        ''')
        
        used_imports = self.analyzer.analyze_code(code)
        self.assertEqual(len(used_imports), 1)
        self.assertIn('import os.path as osp', used_imports)
    
    def test_import_from_alias(self):
        """Test handling 'import from' with aliases."""
        code = dedent('''
            from os.path import join as j, dirname as d
            
            def test_function():
                path = j('a', 'b')
        ''')
        
        used_imports = self.analyzer.analyze_code(code)
        self.assertEqual(len(used_imports), 1)
        self.assertIn('from os.path import join as j, dirname as d', used_imports)
    
    def test_relative_import(self):
        """Test handling relative imports."""
        code = dedent('''
            from .utils import helper
            
            def test_function():
                result = helper()
        ''')
        
        used_imports = self.analyzer.analyze_code(code)
        self.assertEqual(len(used_imports), 1)
        self.assertIn('from .utils import helper', used_imports)
    
    def test_multiple_imports_same_module(self):
        """Test handling multiple imports from same module."""
        code = dedent('''
            from os.path import join
            from os.path import dirname
            
            def test_function():
                path = join('a', dirname('b'))
        ''')
        
        used_imports = self.analyzer.analyze_code(code)
        self.assertEqual(len(used_imports), 2)
        self.assertTrue(any('join' in imp for imp in used_imports))
        self.assertTrue(any('dirname' in imp for imp in used_imports))
    
    def test_nested_attribute_access(self):
        """Test handling nested attribute access."""
        code = dedent('''
            import os
            
            def test_function():
                path = os.path.join.func()
        ''')
        
        used_imports = self.analyzer.analyze_code(code)
        self.assertEqual(len(used_imports), 1)
        self.assertIn('import os', used_imports)


    def test_third_party_import_skipped(self):
        """
        If code does 'import requests' or 'from requests import get', 
        ensure we don't try to parse or attach that library's internal code.
        We just see an import statement, nothing more.
        """
        code = dedent('''
            import requests
            from requests import get

            def do_stuff():
                data = get("http://example.com")
                return data
        ''')

        analyzer = ImportAnalyzer()
        used_imports = analyzer.analyze_code(code)
        # We'll see both imports as used, presumably
        self.assertEqual(len(used_imports), 2)
        self.assertIn('import requests', used_imports)
        self.assertIn('from requests import get', used_imports)

        # But crucially, we won't parse "requests" internally or do anything fancy with it
        # If the tool had a skip-libs logic, we might confirm we never read from site-packages, etc.


if __name__ == '__main__':
    unittest.main()
