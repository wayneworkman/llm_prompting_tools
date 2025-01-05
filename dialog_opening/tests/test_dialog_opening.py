# tests/test_dialog_opening.py (place in ./tests/test_dialog_opening.py)
import os
import unittest
from unittest.mock import patch, ANY
import sys
import tempfile
import shutil
import dialog_opening


class TestDialogOpeningScript(unittest.TestCase):
    @patch('dialog_opening.generate_prompt')
    @patch('os.path.isfile', return_value=True)
    def test_default_arguments(self, mock_isfile, mock_generate_prompt):
        """
        If user does not specify --prompt-instructions,
        we default to 'prompt_instructions.txt' and read it if it exists.
        We also now expect the default output file to be 'prompt.txt' in the current working directory.
        """
        import sys
        import os
        from unittest.mock import patch, ANY
        import dialog_opening

        # Provide the path to the old top-level script (or any placeholder),
        # so we can simulate running "python dialog_opening.py" with no arguments.
        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        with patch.object(sys, 'argv', [test_script]):
            with patch('builtins.print') as mock_print:
                dialog_opening.main()

                # The new default: "prompt.txt" in the user's current directory
                expected_output_file = os.path.join(os.getcwd(), "prompt.txt")

                mock_generate_prompt.assert_called_once_with(
                    input_dir='.',
                    output_file=expected_output_file,
                    prompt_instructions=ANY
                )
                mock_print.assert_any_call(expected_output_file + " generated successfully.")


    @patch('dialog_opening.generate_prompt')
    @patch('os.path.isfile', return_value=False)
    def test_default_arguments_no_file(self, mock_isfile, mock_generate_prompt):
        """
        If user does not specify --prompt-instructions AND prompt_instructions.txt doesn't exist,
        we do NOT fail, but pass an empty string as instructions.
        We also expect the default output file to be prompt.txt in the current working directory.
        """
        import sys
        import os
        from unittest.mock import patch
        import dialog_opening

        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        with patch.object(sys, 'argv', [test_script]):
            with patch('builtins.print') as mock_print:
                dialog_opening.main()

                # Now we expect the default output file to be "prompt.txt" in os.getcwd()
                expected_output_file = os.path.join(os.getcwd(), "prompt.txt")

                mock_generate_prompt.assert_called_once_with(
                    input_dir='.',
                    output_file=expected_output_file,
                    prompt_instructions=""
                )

                # Confirm we printed "generated successfully" message too
                mock_print.assert_any_call(expected_output_file + " generated successfully.")



    @patch('dialog_opening.generate_prompt')
    @patch('os.path.isfile', return_value=False)
    def test_custom_arguments_file_missing(self, mock_isfile, mock_generate_prompt):
        """
        If user explicitly specifies a non-default instructions file AND
        it's not found, we should exit with an error.
        """
        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        custom_dir = '/tmp/custom_dir_for_test'
        custom_output = '/tmp/custom_prompt.txt'
        custom_instructions = 'my_instructions.txt'  # Non-default

        if not os.path.exists(custom_dir):
            os.makedirs(custom_dir, exist_ok=True)

        with patch.object(sys, 'argv', [
            test_script,
            '--input-dir', custom_dir,
            '--output-file', custom_output,
            '--prompt-instructions', custom_instructions
        ]):
            with patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit):
                    dialog_opening.__name__ = "__main__"
                    dialog_opening.main()

                # generate_prompt should NOT be called if we fail first
                mock_generate_prompt.assert_not_called()

                # Check that we printed an error about file not found
                printed_msgs = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("file not found" in msg.lower() for msg in printed_msgs))

        if os.path.exists(custom_dir):
            shutil.rmtree(custom_dir)
        if os.path.exists(custom_output):
            os.remove(custom_output)

    @patch('dialog_opening.generate_prompt')
    @patch('os.path.isfile', return_value=True)
    def test_custom_arguments_file_present(self, mock_isfile, mock_generate_prompt):
        """
        If user explicitly specifies a non-default instructions file
        and it's found, we read it and pass its content.
        """
        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        custom_dir = '/tmp/custom_dir_for_test2'
        custom_output = '/tmp/custom_prompt2.txt'
        custom_instructions = 'my_instructions.txt'  # Non-default

        if not os.path.exists(custom_dir):
            os.makedirs(custom_dir, exist_ok=True)

        with patch.object(sys, 'argv', [
            test_script,
            '--input-dir', custom_dir,
            '--output-file', custom_output,
            '--prompt-instructions', custom_instructions
        ]):
            # We'll mock the file reading so we don't worry about the actual file content
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = "Custom file content"
                with patch('builtins.print') as mock_print:
                    dialog_opening.__name__ = "__main__"
                    dialog_opening.main()

                    mock_generate_prompt.assert_called_once_with(
                        input_dir=custom_dir,
                        output_file=custom_output,
                        prompt_instructions="Custom file content"
                    )
                    mock_print.assert_any_call(custom_output + " generated successfully.")

        if os.path.exists(custom_dir):
            shutil.rmtree(custom_dir)
        if os.path.exists(custom_output):
            os.remove(custom_output)

    @patch('lib.prompt_generation.generate_prompt', side_effect=FileNotFoundError("Directory not found"))
    def test_invalid_input_directory(self, mock_generate_prompt):
        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        invalid_dir = '/nonexistent/path'
        output_file = '/tmp/prompt_test.txt'
        with patch.object(sys, 'argv', [test_script, '--input-dir', invalid_dir, '--output-file', output_file]):
            with patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit):
                    dialog_opening.__name__ = "__main__"
                    dialog_opening.main()
                mock_print.assert_any_call("Directory not found")

    @patch('lib.prompt_generation.generate_prompt', side_effect=PermissionError("No write permissions"))
    def test_no_write_permissions_output_file(self, mock_generate_prompt):
        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        tempdir = tempfile.mkdtemp()
        output_file = os.path.join(tempdir, "prompt.txt")
        os.chmod(tempdir, 0o500)
        with patch.object(sys, 'argv', [test_script, '--output-file', output_file]):
            with patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit):
                    dialog_opening.__name__ = "__main__"
                    dialog_opening.main()
                mock_print.assert_any_call("No write permissions")
        os.chmod(tempdir, 0o700)
        shutil.rmtree(tempdir)

    def test_output_file_is_directory(self):
        """
        Ensure the script fails gracefully if --output-file points to a directory.
        """
        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use the directory itself as the "output file"
            with patch.object(sys, 'argv', [test_script, '--output-file', tmpdir]):
                with patch('builtins.print') as mock_print:
                    with self.assertRaises(SystemExit):
                        dialog_opening.__name__ = "__main__"
                        dialog_opening.main()
                    messages = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("No write permissions" in msg or "Directory not found" in msg for msg in messages))

if __name__ == '__main__':
    unittest.main()
