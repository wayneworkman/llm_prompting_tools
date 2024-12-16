# tests/test_gitignore_utils.py (place in ./tests/test_gitignore_utils.py)
import unittest
import tempfile
import os
from lib.gitignore_utils import load_gitignore_patterns, should_include_file

class TestGitignoreUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_empty_gitignore(self):
        patterns = load_gitignore_patterns(self.root)
        self.assertEqual(patterns, [])

    def test_load_gitignore_patterns(self):
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("# comment\n")
            f.write("*.pyc\n")
            f.write("secret.txt\n")

        patterns = load_gitignore_patterns(self.root)
        self.assertIn("*.pyc", patterns)
        self.assertIn("secret.txt", patterns)

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

        patterns = load_gitignore_patterns(self.root)

        self.assertFalse(should_include_file(os.path.join(self.root, "test.pyc"), self.root, patterns))
        self.assertFalse(should_include_file(os.path.join(self.root, "excluded_dir"), self.root, patterns))
        self.assertTrue(should_include_file(os.path.join(self.root, "normal.txt"), self.root, patterns))

    def test_exclude_dot_git(self):
        # Even without patterns, .git directories should be excluded
        git_path = os.path.join(self.root, ".git")
        os.makedirs(git_path)
        self.assertFalse(should_include_file(git_path, self.root, []))

    def test_anchored_patterns(self):
        # Test anchored patterns (starting with '/')
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("/anchored.txt\n")
            f.write("*.log\n")

        patterns = load_gitignore_patterns(self.root)
        anchored_path = os.path.join(self.root, "anchored.txt")
        with open(anchored_path, 'w') as f:
            f.write("root file")
        log_path = os.path.join(self.root, "data.log")
        with open(log_path, 'w') as f:
            f.write("logfile")

        # anchored.txt is at the root and should be excluded by anchored pattern
        self.assertFalse(should_include_file(anchored_path, self.root, patterns))
        # data.log should also be excluded by *.log pattern
        self.assertFalse(should_include_file(log_path, self.root, patterns))

    def test_directory_pattern_with_subdirs(self):
        # Test a directory pattern with trailing slash
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("subdir/\n")

        patterns = load_gitignore_patterns(self.root)
        os.makedirs(os.path.join(self.root, "subdir", "nested"))
        with open(os.path.join(self.root, "subdir", "nested", "file.txt"), 'w') as f:
            f.write("nested file")

        # subdir and all contents should be excluded
        self.assertFalse(should_include_file(os.path.join(self.root, "subdir"), self.root, patterns))
        self.assertFalse(should_include_file(os.path.join(self.root, "subdir", "nested"), self.root, patterns))
        self.assertFalse(should_include_file(os.path.join(self.root, "subdir", "nested", "file.txt"), self.root, patterns))

    def test_complex_patterns(self):
        # Test multiple complex patterns
        gitignore_path = os.path.join(self.root, '.gitignore')
        with open(gitignore_path, 'w') as f:
            f.write("**/temp/*.tmp\n")
            f.write("!**/temp/keep_me.tmp\n")

        patterns = load_gitignore_patterns(self.root)
        os.makedirs(os.path.join(self.root, "a", "temp"))
        with open(os.path.join(self.root, "a", "temp", "file.tmp"), 'w') as f:
            f.write("temp file")
        with open(os.path.join(self.root, "a", "temp", "keep_me.tmp"), 'w') as f:
            f.write("keep this file")

        # file.tmp should be excluded
        self.assertFalse(should_include_file(os.path.join(self.root, "a", "temp", "file.tmp"), self.root, patterns))
        # keep_me.tmp should be included due to the negation pattern
        self.assertTrue(should_include_file(os.path.join(self.root, "a", "temp", "keep_me.tmp"), self.root, patterns))

if __name__ == '__main__':
    unittest.main()
