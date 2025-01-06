import unittest
import tempfile
import os
import stat

from lib.gitignore_utils import load_gitignore_spec, should_include_file, find_gitignore_file

class TestGitignoreUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_empty_gitignore(self):
        # If there is no .gitignore file, load_gitignore_spec should return an empty PathSpec
        gitignore_spec = load_gitignore_spec(self.root)
        # Just ensure it doesn't raise an error. It's "empty" from pathspec's perspective.
        self.assertIsNotNone(gitignore_spec)

    def test_load_gitignore_patterns(self):
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("# comment\n")
            f.write("*.pyc\n")
            f.write("secret.txt\n")

        gitignore_spec = load_gitignore_spec(self.root)
        self.assertTrue(gitignore_spec.match_file("test.pyc"))
        self.assertTrue(gitignore_spec.match_file("secret.txt"))
        self.assertFalse(gitignore_spec.match_file("normal.txt"))

    def test_find_gitignore_in_parent(self):
        # Create .gitignore in root
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n")

        # Create nested directories
        nested_dir = os.path.join(self.root, "level1", "level2", "level3")
        os.makedirs(nested_dir)

        # Find .gitignore from nested directory
        found_path, found_root = find_gitignore_file(nested_dir)
        self.assertEqual(found_path, gitignore_path)
        self.assertEqual(found_root, self.root)

        # Verify patterns work from nested directory
        gitignore_spec = load_gitignore_spec(nested_dir)
        self.assertTrue(gitignore_spec.match_file("test.pyc"))

    def test_stop_at_git_directory(self):
        # Create nested structure with .git directory in the middle
        mid_dir = os.path.join(self.root, "level1")
        nested_dir = os.path.join(mid_dir, "level2")
        os.makedirs(nested_dir)
        
        # Create .git directory in mid_dir
        os.makedirs(os.path.join(mid_dir, ".git"))
        
        # Create .gitignore in root (should not be found)
        with open(os.path.join(self.root, '.gitignore'), 'w') as f:
            f.write("*.pyc\n")

        # Search from nested_dir - should stop at mid_dir due to .git
        found_path, found_root = find_gitignore_file(nested_dir)
        self.assertIsNone(found_path)  # No .gitignore found
        self.assertEqual(found_root, mid_dir)  # But found repo root

    def test_handle_permission_denied(self):
        # Create a nested directory for testing
        nested_dir = os.path.join(self.root, "level1", "level2")
        os.makedirs(nested_dir)
        
        # Create .gitignore in root (should never be found due to permission error)
        with open(os.path.join(self.root, '.gitignore'), 'w') as f:
            f.write("*.pyc\n")

        # Store original os.path.dirname to restore later
        original_dirname = os.path.dirname
        
        def mock_dirname(path):
            # Raise PermissionError when trying to access parent of level2
            if path.endswith('level2'):
                raise PermissionError("Permission denied")
            return original_dirname(path)
            
        try:
            # Replace os.path.dirname with our mock version
            os.path.dirname = mock_dirname
            
            # Test should now encounter PermissionError and return None
            found_path, found_root = find_gitignore_file(nested_dir)
            self.assertIsNone(found_path)
            self.assertIsNone(found_root)
        finally:
            # Restore original os.path.dirname
            os.path.dirname = original_dirname

    def test_should_include_file(self):
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n")
            f.write("excluded_dir/\n")

        # Create files and dirs
        with open(os.path.join(self.root, "test.pyc"), 'w') as f:
            f.write("bytecode")

        os.makedirs(os.path.join(self.root, "excluded_dir"))
        with open(os.path.join(self.root, "excluded_dir", "file.txt"), 'w') as f:
            f.write("secret")

        gitignore_spec = load_gitignore_spec(self.root)

        # test.pyc should be excluded
        self.assertFalse(should_include_file(os.path.join(self.root, "test.pyc"), self.root, gitignore_spec))
        # the entire excluded_dir is excluded
        self.assertFalse(should_include_file(os.path.join(self.root, "excluded_dir"), self.root, gitignore_spec))
        # normal.txt (which doesn't exist, but let's test logic) should be included
        self.assertTrue(should_include_file(os.path.join(self.root, "normal.txt"), self.root, gitignore_spec))

    def test_exclude_dot_git(self):
        # Even without patterns, .git directories should be excluded
        git_path = os.path.join(self.root, ".git")
        os.makedirs(git_path)
        empty_spec = load_gitignore_spec(self.root)
        self.assertFalse(should_include_file(git_path, self.root, empty_spec))

    def test_anchored_patterns(self):
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("/anchored.txt\n")
            f.write("*.log\n")

        gitignore_spec = load_gitignore_spec(self.root)
        anchored_path = os.path.join(self.root, "anchored.txt")
        with open(anchored_path, 'w') as f:
            f.write("root file")
        log_path = os.path.join(self.root, "data.log")
        with open(log_path, 'w') as f:
            f.write("logfile")

        self.assertFalse(should_include_file(anchored_path, self.root, gitignore_spec))
        self.assertFalse(should_include_file(log_path, self.root, gitignore_spec))

    def test_multiple_gitignore_files(self):
        """Test that only the first .gitignore found (going up) is used"""
        # Create nested structure
        nested_dir = os.path.join(self.root, "level1", "level2")
        os.makedirs(nested_dir)
        
        # Create .gitignore in nested_dir
        with open(os.path.join(nested_dir, '.gitignore'), 'w') as f:
            f.write("*.txt\n")
            
        # Create .gitignore in root
        with open(os.path.join(self.root, '.gitignore'), 'w') as f:
            f.write("*.pyc\n")
            
        # Test from nested_dir
        gitignore_spec = load_gitignore_spec(nested_dir)
        
        # Should match *.txt but not *.pyc
        self.assertTrue(gitignore_spec.match_file("test.txt"))
        self.assertFalse(gitignore_spec.match_file("test.pyc"))

    def test_root_directory_handling(self):
        """Test behavior when reaching root directory"""
        # This test might not work on Windows, so we'll skip it
        if os.name == 'nt':
            return
            
        # Start from root directory
        found_path, found_root = find_gitignore_file('/')
        self.assertIsNone(found_path)
        self.assertIsNone(found_root)

if __name__ == '__main__':
    unittest.main()