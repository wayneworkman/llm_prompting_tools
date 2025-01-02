# tests/test_listing.py (place in ./tests/test_listing.py)
import unittest
import tempfile
import os
import stat
from unittest.mock import patch

from lib.listing import recursive_list

# Import pathspec so we can create an empty spec for tests
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

class TestListing(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name
        # Create some test files and directories
        os.makedirs(os.path.join(self.root, 'subdir'))
        with open(os.path.join(self.root, 'file1.txt'), 'w') as f:
            f.write("test file 1")
        with open(os.path.join(self.root, 'subdir', 'file2.txt'), 'w') as f:
            f.write("test file 2")

    def tearDown(self):
        self.temp_dir.cleanup()

    def empty_gitignore_spec(self):
        """Helper to return an empty PathSpec (no patterns)."""
        return PathSpec.from_lines(GitWildMatchPattern, [])

    @patch('lib.listing.should_include_file', return_value=True)
    def test_recursive_list_all_included(self, mock_should_include):
        gitignore_spec = self.empty_gitignore_spec()
        lines = recursive_list(self.root, self.root, gitignore_spec)
        joined = "\n".join(lines)
        self.assertIn("file1.txt", joined)
        self.assertIn("subdir:", joined)
        self.assertIn("file2.txt", joined)

    @patch('lib.listing.should_include_file')
    def test_recursive_list_excludes(self, mock_should_include):
        # Mock so that file2.txt is excluded
        def side_effect(path, root_path, spec):
            if 'file2.txt' in path:
                return False
            return True

        mock_should_include.side_effect = side_effect
        gitignore_spec = self.empty_gitignore_spec()
        lines = recursive_list(self.root, self.root, gitignore_spec)
        joined = "\n".join(lines)
        self.assertIn("file1.txt", joined)
        self.assertNotIn("file2.txt", joined)  # excluded

    def test_recursive_list_empty_directory(self):
        # Test listing on an empty directory
        empty_dir = os.path.join(self.root, "empty")
        os.makedirs(empty_dir)
        gitignore_spec = self.empty_gitignore_spec()
        lines = recursive_list(empty_dir, empty_dir, gitignore_spec)
        joined = "\n".join(lines)
        self.assertIn(os.path.abspath(empty_dir) + ":", joined)
        self.assertIn("total 0", joined)
        # No files or subdirs should be listed beyond total 0

    def test_recursive_list_nested_directories(self):
        # Create nested directories several levels deep
        nested_dir = os.path.join(self.root, "nested", "level1", "level2")
        os.makedirs(nested_dir)
        file_path = os.path.join(nested_dir, "deep_file.txt")
        with open(file_path, 'w') as f:
            f.write("deep content")

        gitignore_spec = self.empty_gitignore_spec()
        lines = recursive_list(self.root, self.root, gitignore_spec)
        joined = "\n".join(lines)
        self.assertIn("nested:", joined)
        self.assertIn("level1:", joined)
        self.assertIn("level2:", joined)
        self.assertIn("deep_file.txt", joined)

    @unittest.skipIf(os.name == 'nt', "Symlinks are not always enabled on Windows by default.")
    def test_recursive_list_symlink(self):
        # Test listing that includes a symlink
        link_source = os.path.join(self.root, "file1.txt")
        link_target = os.path.join(self.root, "link_to_file1")
        os.symlink(link_source, link_target)
        gitignore_spec = self.empty_gitignore_spec()
        lines = recursive_list(self.root, self.root, gitignore_spec)
        joined = "\n".join(lines)
        # Should list link_to_file1 as well
        self.assertIn("link_to_file1", joined)

if __name__ == '__main__':
    unittest.main()
