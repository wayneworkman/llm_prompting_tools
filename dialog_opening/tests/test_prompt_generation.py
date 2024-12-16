# tests/test_prompt_generation.py (place in ./tests/test_prompt_generation.py)

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch
from lib.prompt_generation import generate_prompt

class TestPromptGeneration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name
        with open(os.path.join(self.root, "README.md"), "w") as f:
            f.write("# Test Project\nThis is a test.")

        with open(os.path.join(self.root, "code.py"), "w") as f:
            f.write("print('Hello World')")

        with open(os.path.join(self.root, "SPECIAL_PROMPT_INSTRUCTIONS.txt"), "w") as f:
            f.write("These are special instructions.\nAnalyze the code thoroughly.")

        with open(os.path.join(self.root, "binary.dat"), "wb") as f:
            f.write(b'\x00\xFF\x00')

        with open(os.path.join(self.root, "a_fences.md"), "w") as f:
            f.write("A file with code fences:\n```\nSome code here\n```")

        with open(os.path.join(self.root, "notes.txt"), "w") as f:
            f.write("Some plain text data.")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('lib.prompt_generation.recursive_list')
    def test_generate_prompt(self, mock_recursive_list):
        # Mock recursive_list to return a simulated directory structure listing
        mock_recursive_list.return_value = [
            f"{os.path.abspath(self.root)}:",
            "total 8",
            "-rw-rw-r-- 1 user group 123 Jan 01 00:00 README.md",
            "-rw-rw-r-- 1 user group 456 Jan 01 00:00 code.py",
            ""
        ]
        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file)

        self.assertTrue(os.path.isfile(output_file))
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("README.md", content)
            self.assertIn("code.py", content)
            self.assertIn("These are special instructions.", content)  # From SPECIAL_PROMPT_INSTRUCTIONS

    def test_generate_prompt_includes_special_instructions(self):
        # Test that the prompt includes the special instructions when the file is present.
        output_file = os.path.join(self.root, "prompt.txt")
        # Run without mocks for integration test
        generate_prompt(self.root, output_file)

        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("These are special instructions.", content)

    def test_generate_prompt_no_special_instructions_file(self):
        # Remove SPECIAL_PROMPT_INSTRUCTIONS.txt to test behavior without it
        os.remove(os.path.join(self.root, "SPECIAL_PROMPT_INSTRUCTIONS.txt"))
        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file)
        with open(output_file, 'r') as f:
            content = f.read()
            # Ensure that prompt still generates even without special instructions
            self.assertIn("README.md", content)
            # Confirm no special instructions present
            self.assertNotIn("These are special instructions.", content)

    def test_generate_prompt_markdown_code_fences(self):
        # Test markdown file with code fences should be enclosed in START/END markers
        md_path = os.path.join(self.root, "example.md")
        with open(md_path, "w") as f:
            f.write("```\nprint('Inside code fence')\n```")
        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file)

        with open(output_file, 'r') as f:
            content = f.read()
            # Expect START/END for files containing code fences
            self.assertIn("START OF MARKDOWN FILE WITH CODE FENCES", content)
            self.assertIn("END OF MARKDOWN FILE WITH CODE FENCES", content)
            self.assertIn("print('Inside code fence')", content)

    def test_generate_prompt_only_markdown_no_fences(self):
        # Test markdown file without code fences should be enclosed in triple backticks
        # Remove README and code.py to test only markdown scenario
        os.remove(os.path.join(self.root, "README.md"))
        os.remove(os.path.join(self.root, "code.py"))

        md_path = os.path.join(self.root, "info.md")
        with open(md_path, "w") as f:
            f.write("# Info\nThis markdown has no code fences.")
        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file)
        with open(output_file, 'r') as f:
            content = f.read()
            # Should be in triple backticks since no code fences detected
            self.assertIn("```", content)
            self.assertIn("This markdown has no code fences.", content)

    def test_generate_prompt_integration_real_files(self):
        # Create a variety of files: non-markdown text, binary, markdown with and without fences.
        # We'll name the fences file as `a_fences.md` and the no-fences file as `z_nofences.md`
        # so that alphabetically a_fences.md appears before z_nofences.md. This ensures that any
        # code fences appear before z_nofences.md in the file contents section.

        bin_path = os.path.join(self.root, "binary.dat")
        with open(bin_path, "wb") as f:
            f.write(b'\x00\xFF\x00')

        a_md_fences_path = os.path.join(self.root, "a_fences.md")
        with open(a_md_fences_path, "w") as f:
            f.write("A file with code fences:\n```\nSome code here\n```")

        z_md_no_fences_path = os.path.join(self.root, "z_nofences.md")
        with open(z_md_no_fences_path, "w") as f:
            f.write("# Just some text\nNo code fences here.")

        txt_path = os.path.join(self.root, "notes.txt")
        with open(txt_path, "w") as f:
            f.write("Some plain text data.")

        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file)

        with open(output_file, 'r') as f:
            content = f.read()

            # Check presence of instructions
            self.assertIn("These are special instructions.", content)

            # Binary file should be wrapped in triple backticks
            self.assertIn("```", content)

            # a_fences.md should have START/END markers
            self.assertIn("START OF MARKDOWN FILE WITH CODE FENCES", content)
            self.assertIn("END OF MARKDOWN FILE WITH CODE FENCES", content)

            # z_nofences.md should be enclosed in triple backticks
            self.assertIn("# Just some text", content)

            # Only consider the file contents section, not the directory structure.
            # Find where the file contents start.
            contents_start = content.index("Below are the file contents:")

            # Now find z_nofences.md after contents_start
            z_nofences_index = content.index("z_nofences.md", contents_start)

            # After z_nofences.md appears in the file contents section, ensure no code fences appear again.
            # Since a_fences.md is printed first in the file contents, no fences should appear after z_nofences.md.
            self.assertNotIn("START OF MARKDOWN FILE WITH CODE FENCES", content[z_nofences_index:])

            # notes.txt should be in triple backticks
            self.assertIn("Some plain text data.", content)


if __name__ == '__main__':
    unittest.main()
