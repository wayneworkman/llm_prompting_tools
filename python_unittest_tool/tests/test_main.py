# tests/test_main.py

"""
Tests for main module.
"""
import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import argparse
import sys
import os
import tempfile
from textwrap import dedent

from python_unittest_tool import main
from python_unittest_tool.test_runner import TestRunResult
from python_unittest_tool.test_parser import TestFailure
from python_unittest_tool.code_extractor import CodeSegment


class TestMain(unittest.TestCase):
    """Test cases for main module functionality."""

    def setUp(self):
        """Set up test cases."""
        self.default_args = [
            '--project-root', '.',
            '--test-dir', 'tests',
            '--number-of-issues', '1',
            '--output-file', 'prompt.txt'
        ]

    def test_parse_args_defaults(self):
        """Test parsing command line arguments with defaults."""
        with patch('sys.argv', ['script.py']):
            config = main.parse_args()
            
            self.assertEqual(config.test_dir, 'tests')
            self.assertEqual(config.number_of_issues, 1)
            self.assertEqual(config.output_file, 'prompt.txt')
            self.assertEqual(config.project_root, str(Path('.').resolve()))

    def test_parse_args_custom(self):
        """Test parsing command line arguments with custom values."""
        with patch('sys.argv', ['script.py'] + [
            '--project-root', '/custom/path',
            '--test-dir', 'custom_tests',
            '--number-of-issues', '2',
            '--output-file', 'custom.txt'
        ]):
            config = main.parse_args()
            
            self.assertEqual(config.test_dir, 'custom_tests')
            self.assertEqual(config.number_of_issues, 2)
            self.assertEqual(config.output_file, 'custom.txt')
            self.assertEqual(config.project_root, str(Path('/custom/path').resolve()))

    @patch('python_unittest_tool.main.TestRunner')
    @patch('python_unittest_tool.main.TestOutputParser')
    @patch('python_unittest_tool.main.CodeExtractor')
    @patch('python_unittest_tool.main.DependencyTracker')
    @patch('python_unittest_tool.main.PromptGenerator')
    def test_successful_run_no_failures(self, mock_prompt_gen, mock_dep_track, 
                                      mock_code_ext, mock_parser, mock_runner):
        """Test successful run with no test failures."""
        # Setup mocks
        mock_runner_instance = mock_runner.return_value
        mock_runner_instance.run_tests.return_value = TestRunResult(
            stdout="OK",
            stderr="",
            return_code=0
        )

        # Run analysis
        with patch('sys.argv', ['script.py']):
            exit_code = main.main()

        # Verify
        self.assertEqual(exit_code, 0)
        mock_runner_instance.run_tests.assert_called_once()
        mock_parser.return_value.parse_output.assert_not_called()
        mock_prompt_gen.return_value.generate_prompt.assert_not_called()

    @patch('python_unittest_tool.main.TestRunner')
    @patch('python_unittest_tool.main.TestOutputParser')
    @patch('python_unittest_tool.main.CodeExtractor')
    @patch('python_unittest_tool.main.DependencyTracker')
    @patch('python_unittest_tool.main.PromptGenerator')
    def test_successful_run_with_failures(self, mock_prompt_gen, mock_dep_track, 
                                        mock_code_ext, mock_parser, mock_runner):
        """Test successful run with test failures."""
        # Setup mocks
        mock_runner_instance = mock_runner.return_value
        mock_runner_instance.run_tests.return_value = TestRunResult(
            stdout="FAIL",
            stderr="",
            return_code=1
        )

        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.parse_output.return_value = [
            TestFailure(
                test_name="test_something",
                test_class="TestClass",
                file_path="/test/path",
                line_number=10,
                failure_message="Assert failed",
                traceback="Traceback...",
                full_output="Full output..."
            )
        ]

        mock_code_ext_instance = mock_code_ext.return_value
        mock_code_ext_instance.extract_test_code.return_value = CodeSegment(
            file_path="/test/path",
            class_name="TestClass",
            setup_code=None,
            teardown_code=None,
            test_code="def test_something(): ...",
            source_code=None,
            imports=[]
        )

        mock_dep_track_instance = mock_dep_track.return_value
        mock_dep_track_instance.track_dependencies.return_value = []

        # Run analysis
        with patch('sys.argv', ['script.py']):
            exit_code = main.main()

        # Verify
        self.assertEqual(exit_code, 0)
        mock_runner_instance.run_tests.assert_called_once()
        mock_parser_instance.parse_output.assert_called_once()
        mock_prompt_gen.return_value.generate_prompt.assert_called_once()

    @patch('python_unittest_tool.main.TestRunner')
    def test_test_runner_error(self, mock_runner):
        """Test handling of TestRunner errors."""
        # Setup mock to raise an error
        mock_runner_instance = mock_runner.return_value
        mock_runner_instance.run_tests.side_effect = Exception("Test run failed")

        # Run analysis
        with patch('sys.argv', ['script.py']):
            exit_code = main.main()

        # Verify
        self.assertEqual(exit_code, 1)
        mock_runner_instance.run_tests.assert_called_once()

    @patch('python_unittest_tool.main.TestRunner')
    @patch('python_unittest_tool.main.TestOutputParser')
    @patch('python_unittest_tool.main.CodeExtractor')
    @patch('python_unittest_tool.main.DependencyTracker')
    @patch('python_unittest_tool.main.PromptGenerator')
    def test_prompt_generator_error(self, mock_prompt_gen, mock_dep_track, 
                                    mock_code_ext, mock_parser, mock_runner):
        """Test handling of PromptGenerator errors."""
        mock_runner_instance = mock_runner.return_value
        mock_runner_instance.run_tests.return_value = TestRunResult(
            stdout=(
                "FAIL: test_something (test_module.TestClass)\n"
                "Traceback...\n"
                'File "/test/path", line 10\n'
                "AssertionError: some error\n"
            ),
            stderr="",
            return_code=1
        )

        mock_parser_instance = mock_parser.return_value
        mock_parser_instance.parse_output.return_value = [
            TestFailure(
                test_name="test_something",
                test_class="TestClass",
                file_path="/test/path",
                line_number=10,
                failure_message="Assert failed",
                traceback="Traceback...",
                full_output="FAIL block"
            )
        ]

        # IMPORTANT: Ensure CodeExtractor returns a valid CodeSegment
        mock_code_ext_instance = mock_code_ext.return_value
        mock_code_ext_instance.extract_test_code.return_value = CodeSegment(
            file_path="/test/path",
            class_name="TestClass",
            setup_code=None,
            teardown_code=None,
            test_code="def test_something(): pass",
            source_code=None,
            imports=[]
        )

        # Make prompt generation fail with an Exception
        mock_prompt_gen.return_value.generate_prompt.side_effect = Exception("Failed to write prompt")

        with patch('sys.argv', ['script.py']):
            exit_code = main.main()

        # Confirm we returned 1, and that generate_prompt was indeed called once
        self.assertEqual(exit_code, 1)
        mock_prompt_gen.return_value.generate_prompt.assert_called_once()

    def test_invalid_arguments(self):
        """Test handling of invalid command line arguments."""
        with patch('sys.argv', ['script.py', '--invalid-arg']):
            with self.assertRaises(SystemExit):
                main.parse_args()

    def test_negative_number_of_issues(self):
        """Test handling of negative number of issues."""
        with patch('sys.argv', ['script.py', '--number-of-issues', '-1']):
            with self.assertRaises(SystemExit):
                main.parse_args()

    def test_number_of_issues_zero_means_unlimited(self):
        """
        Ensure that specifying --number-of-issues=0 includes all discovered test failures.
        """
        with patch('sys.argv', ['script.py', 
                                '--project-root', '.', 
                                '--test-dir', 'tests',
                                '--number-of-issues', '0',
                                '--output-file', 'prompt.txt']):
            with patch('python_unittest_tool.main.TestRunner') as mock_runner, \
                 patch('python_unittest_tool.main.TestOutputParser') as mock_parser, \
                 patch('python_unittest_tool.main.CodeExtractor') as mock_code_extractor, \
                 patch('python_unittest_tool.main.DependencyTracker'), \
                 patch('python_unittest_tool.main.PromptGenerator') as mock_gen:

                from python_unittest_tool.code_extractor import CodeSegment
                mock_code_extractor_instance = mock_code_extractor.return_value
                mock_code_extractor_instance.extract_test_code.return_value = CodeSegment(
                    file_path='/test/path_0',
                    class_name='TestClass',
                    setup_code=None,
                    teardown_code=None,
                    test_code='def test_0(): pass',
                    source_code=None,
                    imports=[]
                )
                mock_code_extractor_instance.extract_source_code.return_value = CodeSegment(
                    file_path='/test/path_src_0',
                    class_name=None,
                    setup_code=None,
                    teardown_code=None,
                    test_code=None,
                    source_code='def some_helper(): pass',
                    imports=[]
                )

                mock_runner_instance = mock_runner.return_value
                # Fake a return_code=1 => failures
                mock_runner_instance.run_tests.return_value = TestRunResult(
                    stdout="FAIL", stderr="", return_code=1
                )

                # Suppose 3 failures discovered
                mock_parser_instance = mock_parser.return_value
                mock_parser_instance.parse_output.return_value = [
                    TestFailure(test_name=f"test_{i}", test_class="TestClass",
                                file_path=f"/test/path_{i}", line_number=10,
                                failure_message="Boom", traceback="Traceback...",
                                full_output=f"Full failure {i}")
                    for i in range(3)
                ]

                exit_code = main.main()
                self.assertEqual(exit_code, 0)
                # ensure we generated the prompt with all 3
                mock_gen.return_value.generate_prompt.assert_called_once()
                failures_passed = mock_gen.return_value.generate_prompt.call_args[0][0]
                self.assertEqual(len(failures_passed), 3,
                                "We want all 3 failures included because number_of_issues=0 is unlimited.")

    # ---------------------------------------------------------------------
    # NEW TESTS FOR VERSION ARGUMENT
    # ---------------------------------------------------------------------
    @patch('importlib.metadata.version')
    def test_version_argument(self, mock_version):
        """Test that --version shows the correct version and exits."""
        mock_version.return_value = "0.1.0"
        with patch('sys.argv', ['script.py', '--version']):
            with patch('sys.stdout', new=tempfile.SpooledTemporaryFile(mode='w+')) as stdout:
                # We expect a SystemExit once the parser prints version and exits
                with self.assertRaises(SystemExit) as cm:
                    main.main()
                self.assertEqual(cm.exception.code, 0, "Version argument should exit with code 0")

                stdout.seek(0)
                output = stdout.read().strip()
                expected_output = "python_unittest_tool 0.1.0"
                self.assertEqual(output, expected_output, "Should print the correct version string")

    @patch('python_unittest_tool.main.metadata_version')
    def test_version_not_found(self, mock_version):
        """Test graceful handling when version cannot be determined."""
        from importlib.metadata import PackageNotFoundError
        mock_version.side_effect = PackageNotFoundError("Could not find version")
        with patch('sys.argv', ['script.py', '--version']):
            with patch('sys.stdout', new=tempfile.SpooledTemporaryFile(mode='w+')) as stdout:
                with self.assertRaises(SystemExit) as cm:
                    main.main()
                self.assertEqual(cm.exception.code, 0, "Should still exit successfully even if version is unknown")

                stdout.seek(0)
                output = stdout.read().strip()
                expected_output = "python_unittest_tool unknown"
                self.assertEqual(output, expected_output, "Should show 'unknown' when version not found")


if __name__ == '__main__':
    unittest.main()
