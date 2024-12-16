# tests/test_dialog_opening.py (place in ./tests/test_dialog_opening.py)
import os
import unittest
from unittest.mock import patch
import sys
import tempfile
import shutil
import dialog_opening

class TestDialogOpeningScript(unittest.TestCase):
    @patch('dialog_opening.generate_prompt')
    def test_default_arguments(self, mock_generate_prompt):
        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        with patch.object(sys, 'argv', [test_script]):
            with patch('builtins.print') as mock_print:
                dialog_opening.main()
                expected_output_file = os.path.join(os.path.dirname(dialog_opening.__file__), 'prompt.txt')
                mock_generate_prompt.assert_called_once_with('.', expected_output_file)
                mock_print.assert_any_call(expected_output_file + " generated successfully.")

    @patch('dialog_opening.generate_prompt')  # Changed from 'lib.prompt_generation.generate_prompt' to 'dialog_opening.generate_prompt'
    def test_custom_arguments(self, mock_generate_prompt):
        test_script = os.path.join(os.path.dirname(__file__), '..', 'dialog_opening.py')
        custom_dir = '/tmp/custom_dir_for_test'
        custom_output = '/tmp/custom_prompt.txt'

        if not os.path.exists(custom_dir):
            os.makedirs(custom_dir, exist_ok=True)

        with patch.object(sys, 'argv', [test_script, '--input-dir', custom_dir, '--output-file', custom_output]):
            with patch('builtins.print') as mock_print:
                dialog_opening.__name__ = "__main__"
                dialog_opening.main()

                # Now this should pass, as we're patching the correct function
                mock_generate_prompt.assert_called_once_with(custom_dir, custom_output)

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

if __name__ == '__main__':
    unittest.main()
