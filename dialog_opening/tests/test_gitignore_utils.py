import unittest
import tempfile
import os
import stat

from lib.gitignore_utils import load_gitignore_spec, should_include_file, find_ignore_files, find_gitignore_file

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

    def test_load_ignore_patterns(self):
        # Test loading patterns from .ignore file
        ignore_path = os.path.join(self.root, '.ignore')
        with open(ignore_path, 'w') as f:
            f.write("*.log\n")
            f.write("temp/\n")

        gitignore_spec = load_gitignore_spec(self.root)
        self.assertTrue(gitignore_spec.match_file("test.log"))
        self.assertTrue(gitignore_spec.match_file("temp/"))
        self.assertFalse(gitignore_spec.match_file("normal.txt"))

    def test_load_combined_patterns(self):
        # Test loading patterns from both .gitignore and .ignore files
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n")
            f.write("secret.txt\n")

        ignore_path = os.path.join(self.root, '.ignore')
        with open(ignore_path, 'w') as f:
            f.write("*.log\n")
            f.write("temp/\n")

        gitignore_spec = load_gitignore_spec(self.root)
        # Patterns from .gitignore
        self.assertTrue(gitignore_spec.match_file("test.pyc"))
        self.assertTrue(gitignore_spec.match_file("secret.txt"))
        # Patterns from .ignore
        self.assertTrue(gitignore_spec.match_file("test.log"))
        self.assertTrue(gitignore_spec.match_file("temp/"))
        # Not matched by either
        self.assertFalse(gitignore_spec.match_file("normal.txt"))

    def test_find_ignore_files_in_parent(self):
        # Create ignore files in root
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n")
            
        ignore_path = os.path.join(self.root, '.ignore')
        with open(ignore_path, 'w') as f:
            f.write("*.log\n")

        # Create nested directories
        nested_dir = os.path.join(self.root, "level1", "level2", "level3")
        os.makedirs(nested_dir)

        # Find ignore files from nested directory
        found_paths, found_root = find_ignore_files(nested_dir)
        self.assertEqual(len(found_paths), 2)
        self.assertIn(gitignore_path, found_paths)
        self.assertIn(ignore_path, found_paths)
        self.assertEqual(found_root, self.root)

        # Verify patterns work from nested directory
        gitignore_spec = load_gitignore_spec(nested_dir)
        self.assertTrue(gitignore_spec.match_file("test.pyc"))
        self.assertTrue(gitignore_spec.match_file("test.log"))

    def test_backward_compatibility_find_gitignore_file(self):
        # Test that find_gitignore_file still exists for backward compatibility
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n")

        # The old function name should still work
        found_paths, found_root = find_gitignore_file(self.root)
        self.assertIsNotNone(found_paths)
        self.assertEqual(found_root, self.root)

    def test_stop_at_git_directory(self):
        # Create nested structure with .git directory in the middle
        mid_dir = os.path.join(self.root, "level1")
        nested_dir = os.path.join(mid_dir, "level2")
        os.makedirs(nested_dir)
        
        # Create .git directory in mid_dir
        os.makedirs(os.path.join(mid_dir, ".git"))
        
        # Create .gitignore and .ignore in root (should not be found)
        with open(os.path.join(self.root, '.gitignore'), 'w') as f:
            f.write("*.pyc\n")
        with open(os.path.join(self.root, '.ignore'), 'w') as f:
            f.write("*.log\n")

        # Search from nested_dir - should stop at mid_dir due to .git
        found_paths, found_root = find_ignore_files(nested_dir)
        self.assertEqual(len(found_paths), 0)  # No ignore files found
        self.assertEqual(found_root, mid_dir)  # But found repo root

    def test_handle_permission_denied(self):
        # Create a nested directory for testing
        nested_dir = os.path.join(self.root, "level1", "level2")
        os.makedirs(nested_dir)
        
        # Create ignore files in root (should never be found due to permission error)
        with open(os.path.join(self.root, '.gitignore'), 'w') as f:
            f.write("*.pyc\n")
        with open(os.path.join(self.root, '.ignore'), 'w') as f:
            f.write("*.log\n")

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
            
            # Test should now encounter PermissionError and return empty list
            found_paths, found_root = find_ignore_files(nested_dir)
            self.assertEqual(len(found_paths), 0)
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

    def test_multiple_ignore_files_priority(self):
        """Test that patterns from both .gitignore and .ignore are combined"""
        # Create nested structure
        nested_dir = os.path.join(self.root, "level1", "level2")
        os.makedirs(nested_dir)
        
        # Create .gitignore in nested_dir
        with open(os.path.join(nested_dir, '.gitignore'), 'w') as f:
            f.write("*.txt\n")
            
        # Create .ignore in nested_dir
        with open(os.path.join(nested_dir, '.ignore'), 'w') as f:
            f.write("*.md\n")
            
        # Create .gitignore in root
        with open(os.path.join(self.root, '.gitignore'), 'w') as f:
            f.write("*.pyc\n")
            
        # Test from nested_dir
        gitignore_spec = load_gitignore_spec(nested_dir)
        
        # Should match patterns from both files in nested_dir
        self.assertTrue(gitignore_spec.match_file("test.txt"))
        self.assertTrue(gitignore_spec.match_file("test.md"))
        # Should not match pattern from root (we stop at first directory with ignore files)
        self.assertFalse(gitignore_spec.match_file("test.pyc"))

    def test_root_directory_handling(self):
        """Test behavior when reaching root directory"""
        # This test might not work on Windows, so we'll skip it
        if os.name == 'nt':
            return
            
        # Start from root directory
        found_paths, found_root = find_ignore_files('/')
        self.assertEqual(len(found_paths), 0)
        self.assertIsNone(found_root)

    def test_ignore_file_only(self):
        """Test when only .ignore file exists (no .gitignore)"""
        ignore_path = os.path.join(self.root, '.ignore')
        with open(ignore_path, 'w') as f:
            f.write("*.tmp\n")
            f.write("cache/\n")
            f.write("# Comment line\n")
            f.write("\n")  # Empty line
            f.write("debug.log\n")

        gitignore_spec = load_gitignore_spec(self.root)
        self.assertTrue(gitignore_spec.match_file("test.tmp"))
        self.assertTrue(gitignore_spec.match_file("cache/"))
        self.assertTrue(gitignore_spec.match_file("debug.log"))
        self.assertFalse(gitignore_spec.match_file("normal.txt"))

    def test_overlapping_patterns(self):
        """Test when .gitignore and .ignore have overlapping patterns"""
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("*.log\n")
            f.write("temp/\n")

        ignore_path = os.path.join(self.root, '.ignore')
        with open(ignore_path, 'w') as f:
            f.write("*.log\n")  # Duplicate pattern
            f.write("*.tmp\n")  # New pattern

        gitignore_spec = load_gitignore_spec(self.root)
        # Both should work despite duplication
        self.assertTrue(gitignore_spec.match_file("test.log"))
        self.assertTrue(gitignore_spec.match_file("temp/"))
        self.assertTrue(gitignore_spec.match_file("test.tmp"))

if __name__ == '__main__':
    unittest.main()