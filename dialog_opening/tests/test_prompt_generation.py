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

        with open(os.path.join(self.root, "prompt_instructions.txt"), "w") as f:
            f.write("These are prompt instructions.\nAnalyze the code thoroughly.")

        # Create a small binary file for integration testing of binary exclusion
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
        """
        Mocks out the directory listing and verifies the overall prompt file
        is produced with correct structure and included content.
        """
        mock_recursive_list.return_value = [
            f"{os.path.abspath(self.root)}:",
            "total 8",
            "-rw-rw-r-- 1 user group 123 Jan 01 00:00 README.md",
            "-rw-rw-r-- 1 user group 456 Jan 01 00:00 code.py",
            ""
        ]
        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file, prompt_instructions="Custom instructions at the top.")

        self.assertTrue(os.path.isfile(output_file))
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("README.md", content)
            self.assertIn("code.py", content)
            # Check that our custom instructions are included
            self.assertIn("Custom instructions at the top.", content)

    def test_generate_prompt_includes_instructions(self):
        """
        If prompt_instructions are provided, they should appear at the top of the output.
        """
        output_file = os.path.join(self.root, "prompt.txt")
        with open(os.path.join(self.root, "prompt_instructions.txt"), "r") as f:
            instructions_content = f.read()

        generate_prompt(self.root, output_file, prompt_instructions=instructions_content)
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("These are prompt instructions.", content)

    def test_generate_prompt_no_instructions_file(self):
        """
        If generate_prompt is called with prompt_instructions=None (or empty),
        we expect no instructions in the final output. 
        We remove the prompt_instructions.txt to avoid confusion.
        """
        instructions_path = os.path.join(self.root, "prompt_instructions.txt")
        if os.path.isfile(instructions_path):
            os.remove(instructions_path)

        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file, prompt_instructions=None)  
        with open(output_file, 'r') as f:
            content = f.read()
            # Ensure the normal file references appear
            self.assertIn("README.md", content)
            # Because prompt_instructions=None => no instructions are included
            self.assertNotIn("These are prompt instructions.", content)

    def test_generate_prompt_markdown_code_fences(self):
        """
        If a file has triple backticks, it should be wrapped 
        between START and END markers to avoid LLM confusion.
        """
        md_path = os.path.join(self.root, "example.md")
        with open(md_path, "w") as f:
            f.write("```\nprint('Inside code fence')\n```")
        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file, prompt_instructions=None)

        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("START OF FILE WITH CODE FENCES", content)
            self.assertIn("END OF FILE WITH CODE FENCES", content)
            self.assertIn("print('Inside code fence')", content)

    def test_generate_prompt_only_markdown_no_fences(self):
        os.remove(os.path.join(self.root, "README.md"))
        os.remove(os.path.join(self.root, "code.py"))
        md_path = os.path.join(self.root, "info.md")
        with open(md_path, "w") as f:
            f.write("# Info\nThis markdown has no code fences.")
        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file, prompt_instructions=None)
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("```", content)
            self.assertIn("This markdown has no code fences.", content)

    def test_generate_prompt_integration_real_files(self):
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
        with open(os.path.join(self.root, "prompt_instructions.txt"), "r") as f:
            instructions_content = f.read()

        generate_prompt(self.root, output_file, prompt_instructions=instructions_content)

        with open(output_file, 'r') as f:
            content = f.read()
            # Confirm instructions included
            self.assertIn("These are prompt instructions.", content)
            # The binary file => BINARY FILE CONTENTS EXCLUDED
            self.assertIn("binary.dat", content)
            self.assertIn("```BINARY FILE CONTENTS EXCLUDED```", content)
            self.assertIn("START OF FILE WITH CODE FENCES", content)
            self.assertIn("END OF FILE WITH CODE FENCES", content)
            self.assertIn("z_nofences.md", content)
            self.assertIn("# Just some text", content)
            self.assertIn("notes.txt", content)
            self.assertIn("Some plain text data.", content)

    def test_exclude_output_file_from_prompt(self):
        output_file = os.path.join(self.root, "prompt.txt")
        with open(output_file, "w") as f:
            f.write("This is the would-be output file content.")

        generate_prompt(self.root, output_file, prompt_instructions=None)
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertNotIn("This is the would-be output file content.", content)

    def test_large_unusual_file_encodings(self):
        large_file_path = os.path.join(self.root, "large_file.txt")
        with open(large_file_path, "w", encoding='utf-8') as f:
            f.write("0123456789\n" * 10000)

        weird_file_path = os.path.join(self.root, "weird_file.txt")
        with open(weird_file_path, "w", encoding='utf-8') as f:
            f.write("Here are some emojis: 😊🚀🐱‍👓\nAnd some accented characters: á, ñ, ü\n")

        output_file = os.path.join(self.root, "prompt.txt")
        generate_prompt(self.root, output_file, prompt_instructions=None)

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("large_file.txt", content)
            self.assertIn("weird_file.txt", content)
            self.assertIn("Here are some emojis:", content)
            self.assertIn("😊", content)
            self.assertIn("🚀", content)
            self.assertIn("🐱", content)
            self.assertIn("👓", content)

if __name__ == '__main__':
    unittest.main()
