# tests/test_dependency_tracker.py

import unittest
from textwrap import dedent
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import os

from python_unittest_tool.dependency_tracker import DependencyTracker, FunctionNode


class TestDependencyTracker(unittest.TestCase):
    """Test cases for DependencyTracker class."""

    def setUp(self):
        # These three .py files are the minimal stubs needed.
        self.test_files = {
            '/project/main.py': dedent('''
                from utils import helper
                from .local_module import local_func

                def main_function():
                    result = helper()
                    local_result = local_func()
                    return result + local_result
            '''),
            '/project/utils.py': dedent('''
                def helper():
                    return 42
            '''),
            '/project/local_module.py': dedent('''
                def local_func():
                    return 10
            ''')
        }
        self.tracker = DependencyTracker('/project')

    def mock_open_factory(self, test_files):
        """Create a mock open function that serves our test files."""
        def mock_file_open(filename, *args, **kwargs):
            filename = str(Path(filename).resolve())
            if filename in test_files:
                return mock_open(read_data=test_files[filename])(*args, **kwargs)
            raise FileNotFoundError(f"No such file: {filename}")
        return mock_file_open

    @patch('os.walk')
    @patch('builtins.open')
    def test_simple_dependency_tracking(self, mock_file, mock_os_walk):
        """Test tracking simple function dependencies."""
        # 1) Mock file reading
        mock_file.side_effect = self.mock_open_factory(self.test_files)

        # 2) Mock os.walk so /project/main.py, /project/utils.py, /project/local_module.py are "found"
        mock_os_walk.return_value = [
            ('/project', ('subdir',), ('main.py','utils.py','local_module.py')),
            ('/project/subdir', (), ()),
        ]

        # 3) Now actually track dependencies
        result = self.tracker.track_dependencies('/project/main.py', 'main_function')

        # Expect [helper, local_func, main_function]
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].name, 'helper')
        self.assertEqual(result[1].name, 'local_func')
        self.assertEqual(result[2].name, 'main_function')


if __name__ == '__main__':
    unittest.main()
