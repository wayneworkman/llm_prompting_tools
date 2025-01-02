# tests/test_gitignore_utils.py (place in ./tests/test_gitignore_utils.py)

import unittest
import tempfile
import os

# Update these imports to match your new function names
from lib.gitignore_utils import load_gitignore_spec, should_include_file

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
        # We can't directly check the lines from PathSpec easily, but we can test actual matches:
        self.assertTrue(gitignore_spec.match_file("test.pyc"))
        self.assertTrue(gitignore_spec.match_file("secret.txt"))
        self.assertFalse(gitignore_spec.match_file("normal.txt"))

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
        empty_spec = load_gitignore_spec(self.root)  # This should be effectively empty
        self.assertFalse(should_include_file(git_path, self.root, empty_spec))

    def test_anchored_patterns(self):
        # Test anchored patterns (starting with '/')
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

        # anchored.txt is at the root and should be excluded by anchored pattern
        self.assertFalse(should_include_file(anchored_path, self.root, gitignore_spec))
        # data.log should also be excluded by *.log pattern
        self.assertFalse(should_include_file(log_path, self.root, gitignore_spec))

    def test_directory_pattern_with_subdirs(self):
        # Test a directory pattern with trailing slash
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("subdir/\n")

        gitignore_spec = load_gitignore_spec(self.root)
        os.makedirs(os.path.join(self.root, "subdir", "nested"))
        with open(os.path.join(self.root, "subdir", "nested", "file.txt"), 'w') as f:
            f.write("nested file")

        # subdir and all contents should be excluded
        self.assertFalse(should_include_file(os.path.join(self.root, "subdir"), self.root, gitignore_spec))
        self.assertFalse(should_include_file(os.path.join(self.root, "subdir", "nested"), self.root, gitignore_spec))
        self.assertFalse(should_include_file(os.path.join(self.root, "subdir", "nested", "file.txt"), self.root, gitignore_spec))

    def test_complex_patterns(self):
        # Test multiple complex patterns
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("**/temp/*.tmp\n")
            f.write("!**/temp/keep_me.tmp\n")

        gitignore_spec = load_gitignore_spec(self.root)
        os.makedirs(os.path.join(self.root, "a", "temp"))
        with open(os.path.join(self.root, "a", "temp", "file.tmp"), 'w') as f:
            f.write("temp file")
        with open(os.path.join(self.root, "a", "temp", "keep_me.tmp"), 'w') as f:
            f.write("keep this file")

        # file.tmp should be excluded
        self.assertFalse(should_include_file(os.path.join(self.root, "a", "temp", "file.tmp"), self.root, gitignore_spec))
        # keep_me.tmp should be included due to the negation pattern
        self.assertTrue(should_include_file(os.path.join(self.root, "a", "temp", "keep_me.tmp"), self.root, gitignore_spec))


if __name__ == '__main__':
    unittest.main()
