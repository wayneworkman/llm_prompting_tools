# tests/test_dependency_tracker.py

import unittest
from textwrap import dedent
from pathlib import Path
from unittest.mock import patch, mock_open

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
        self.assertEqual({n.name for n in result}, {"helper", "local_func", "main_function"})



    def test_circular_dependency_tracking(self):
        """
        Ensure that if function A calls B and B calls A, we don't infinite-loop
        and we include both A and B exactly once.
        """
        test_files = {
            '/project/a.py': dedent('''
                from b import func_b

                def func_a():
                    return func_b() + 1
            '''),
            '/project/b.py': dedent('''
                from a import func_a

                def func_b():
                    return func_a() + 10
            '''),
        }

        def mock_open_factory(files):
            def _mopen(filename, *args, **kwargs):
                filename = str(Path(filename).resolve())
                if filename in files:
                    return mock_open(read_data=files[filename])(*args, **kwargs)
                raise FileNotFoundError(f"No such file: {filename}")
            return _mopen

        with patch('os.walk') as mock_walk, \
            patch('builtins.open') as mock_file:
            # Pretend we see a.py and b.py in /project
            mock_walk.return_value = [
                ('/project', [], ('a.py','b.py'))
            ]
            mock_file.side_effect = mock_open_factory(test_files)

            tracker = DependencyTracker('/project')
            # track dependencies starting from a.py => func_a
            result = tracker.track_dependencies('/project/a.py', 'func_a')

            # We expect 2 results: func_a, func_b
            self.assertEqual(len(result), 2, "Should see both func_a and func_b, no duplicates, no infinite loop.")
            names = {node.name for node in result}
            self.assertEqual(names, {'func_a', 'func_b'})

if __name__ == '__main__':
    unittest.main()
