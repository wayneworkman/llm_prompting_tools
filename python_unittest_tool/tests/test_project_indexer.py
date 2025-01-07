# tests/test_project_indexer.py
# (This file goes in the tests/ directory.)

"""
Tests for project_indexer module.
"""

import os
import unittest
import tempfile
import shutil
from pathlib import Path
from python_unittest_tool.project_indexer import ProjectIndexer


class TestProjectIndexer(unittest.TestCase):
    """Test cases for ProjectIndexer class."""

    def setUp(self):
        """
        Create a temporary directory structure for testing. We'll populate it
        with some .py files (and possibly subdirectories) to validate scanning
        and module resolution.
        """
        self.test_dir = tempfile.mkdtemp(prefix="proj_indexer_test_")

        # Construct a minimal project layout
        #
        # self.test_dir/
        # ├── __init__.py
        # ├── main.py
        # ├── utils.py
        # ├── subpkg/
        # │   ├── __init__.py
        # │   └── sub_module.py
        # └── not_python.txt
        #
        # We'll test how ProjectIndexer picks these up.

        Path(self.test_dir, "__init__.py").write_text("# Root package init\n", encoding="utf-8")
        Path(self.test_dir, "main.py").write_text("def main_func(): pass\n", encoding="utf-8")
        Path(self.test_dir, "utils.py").write_text("def util_func(): pass\n", encoding="utf-8")

        subpkg_dir = Path(self.test_dir, "subpkg")
        subpkg_dir.mkdir()
        Path(subpkg_dir, "__init__.py").write_text("# subpkg init\n", encoding="utf-8")
        Path(subpkg_dir, "sub_module.py").write_text("def sub_func(): pass\n", encoding="utf-8")

        # A non-python file that should be ignored by scanning
        Path(self.test_dir, "not_python.txt").write_text("Just a text file\n", encoding="utf-8")

        self.indexer = ProjectIndexer(self.test_dir)

    def tearDown(self):
        """
        Clean up the temporary directory after tests.
        """
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_basic_scanning(self):
        """
        Test that the project indexer correctly discovers our .py files and
        populates module_map as expected.
        """
        # The module_map might have:
        #   "" (if it tries to treat the root __init__.py) – typically won't store empty string as a module
        #   "main" -> /.../main.py
        #   "utils" -> /.../utils.py
        #   "subpkg.__init__" -> /.../subpkg/__init__.py
        #   "subpkg.sub_module" -> /.../subpkg/sub_module.py
        #
        # We'll check presence of these keys.
        module_keys = sorted(self.indexer.module_map.keys())
        self.assertIn("main", module_keys, "Expected 'main.py' to appear in module_map.")
        self.assertIn("utils", module_keys, "Expected 'utils.py' to appear in module_map.")
        self.assertIn("subpkg.__init__", module_keys, "Expected subpkg/__init__.py to appear in module_map.")
        self.assertIn("subpkg.sub_module", module_keys, "Expected subpkg/sub_module.py to appear in module_map.")
        self.assertNotIn("not_python", module_keys, "Non-Python file should not appear in module_map.")

        # Confirm the file paths themselves match
        main_path = self.indexer.module_map["main"]
        self.assertTrue(main_path.name == "main.py", "main.py not recognized properly.")

        sub_module_path = self.indexer.module_map["subpkg.sub_module"]
        self.assertTrue(sub_module_path.name == "sub_module.py", "sub_module.py not recognized properly.")

    def test_resolve_module(self):
        """
        Test that resolve_module can locate a module by name or dotted path from
        the root folder. 
        """
        # For direct usage from the test_dir, let's pretend base_file is main.py 
        base_file = str(Path(self.test_dir, "main.py"))

        # Should find 'utils'
        utils_path = self.indexer.resolve_module(base_file, "utils", level=0)
        self.assertIsNotNone(utils_path, "Expected to resolve 'utils' module.")
        self.assertTrue(utils_path.endswith("utils.py"))

        # Should find 'subpkg.sub_module'
        sub_module_path = self.indexer.resolve_module(base_file, "subpkg.sub_module", level=0)
        self.assertIsNotNone(sub_module_path, "Expected to resolve 'subpkg.sub_module'.")
        self.assertTrue(sub_module_path.endswith("sub_module.py"))

        # Non-existent module
        bogus_path = self.indexer.resolve_module(base_file, "bogus", level=0)
        self.assertIsNone(bogus_path, "Expected None when resolving a non-existent module.")

    def test_resolve_module_relative_import(self):
        """
        Test that resolve_module can handle relative imports (level > 0).
        For example, from . import sub_module inside subpkg/sub_module.py
        """
        base_file = str(Path(self.test_dir, "subpkg", "sub_module.py"))

        # E.g. "from . import sub_module" within subpkg means level=1, module_str=''
        # We expect it to point to subpkg/__init__.py
        resolved_init = self.indexer.resolve_module(base_file, "", level=1)
        self.assertIsNotNone(resolved_init, "Expected to resolve relative import to subpkg/__init__.py.")
        self.assertTrue(resolved_init.endswith("__init__.py"))

        # Another example: from .. import utils
        # means go up one directory from subpkg -> test_dir, then find 'utils'
        resolved_utils = self.indexer.resolve_module(base_file, "utils", level=2)
        self.assertIsNotNone(resolved_utils, "Expected to resolve relative import of 'utils'.")
        self.assertTrue(resolved_utils.endswith("utils.py"))

        # If we do level=2 but empty module_str, it might look for __init__.py in the project root
        resolved_root_init = self.indexer.resolve_module(base_file, "", level=2)
        self.assertIsNotNone(
            resolved_root_init,
            "Expected to resolve empty module name to the root __init__.py using level=2."
        )
        self.assertTrue(resolved_root_init.endswith("__init__.py"))

    def test_resolve_module_out_of_scope(self):
        """
        Test that if the relative import escapes beyond the project root,
        we end up with None (or some fallback).
        """
        # Let’s simulate going too far up from main.py
        base_file = str(Path(self.test_dir, "main.py"))

        # If we do multiple levels beyond the project root, there's no further scanning
        # so it might fail or return None
        resolved_nothing = self.indexer.resolve_module(base_file, "nonexistent", level=99)
        self.assertIsNone(resolved_nothing, "Expected None when going too many levels up.")

    def test_empty_directory(self):
        """
        Test behavior if the directory is empty or partially cleaned up 
        after initialization.
        """
        # We'll create a brand-new empty directory, re-init an indexer, and ensure no modules.
        empty_dir = tempfile.mkdtemp(prefix="proj_indexer_empty_")
        try:
            new_indexer = ProjectIndexer(empty_dir)
            self.assertEqual(len(new_indexer.module_map), 0, "Expected no modules in an empty directory.")
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_no_python_files(self):
        """
        Test behavior if we only have non-Python files in the directory. 
        Should produce an empty module map.
        """
        no_py_dir = tempfile.mkdtemp(prefix="proj_indexer_nopy_")
        try:
            # Put a text file in it
            Path(no_py_dir, "README.txt").write_text("No python here.", encoding="utf-8")
            # Re-init
            new_indexer = ProjectIndexer(no_py_dir)
            self.assertEqual(len(new_indexer.module_map), 0, "Expected no modules with no .py files present.")
        finally:
            shutil.rmtree(no_py_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()

