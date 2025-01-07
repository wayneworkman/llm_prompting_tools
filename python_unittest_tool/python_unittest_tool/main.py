# python_unittest_tool/main.py
# (This file goes in the python_unittest_tool/ directory.)

"""
Main entry point for the test analysis tool.
"""
import argparse
import sys
import logging
from pathlib import Path
from typing import List
from dataclasses import dataclass

# Updated imports to reference the package:
from python_unittest_tool.test_runner import TestRunner
from python_unittest_tool.test_parser import TestOutputParser
from python_unittest_tool.code_extractor import CodeExtractor
from python_unittest_tool.import_analyzer import ImportAnalyzer
from python_unittest_tool.dependency_tracker import DependencyTracker
from python_unittest_tool.prompt_generator import PromptGenerator, FailureInfo

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration container."""
    project_root: str
    test_dir: str
    number_of_issues: int
    output_file: str


def parse_args() -> Config:
    """
    Parse command line arguments.
    
    Returns:
        Config object containing parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Analyze failing unit tests and generate LLM prompt.'
    )
    
    parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='Root directory of the project (default: current directory)'
    )
    
    parser.add_argument(
        '--test-dir',
        type=str,
        default='tests',
        help='Directory containing tests (default: tests)'
    )
    
    parser.add_argument(
        '--number-of-issues',
        type=int,
        default=1,
        help='Number of test failures to include (0 for all, default: 1)'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        default='prompt.txt',
        help='Output file path (default: prompt.txt)'
    )
    
    args = parser.parse_args()
    
    if args.number_of_issues < 0:
        parser.error("number_of_issues cannot be negative")
    
    return Config(
        project_root=str(Path(args.project_root).resolve()),
        test_dir=args.test_dir,
        number_of_issues=args.number_of_issues,
        output_file=args.output_file
    )


def run_analysis(config: Config) -> int:
    """
    Run the complete test analysis workflow with logic:
    - Return 1 if the test runner fails to run (Exception) or prompt generation fails
    - Return 0 otherwise (including if we have test failures)
    - If test_result has_failures => parse them, else skip parse_output
    """
    try:
        test_runner = TestRunner(config.test_dir)
        test_parser = TestOutputParser(config.number_of_issues)
        code_extractor = CodeExtractor()
        dependency_tracker = DependencyTracker(config.project_root)
        prompt_generator = PromptGenerator(config.project_root)
        
        import_analyzer = ImportAnalyzer()

        logger.info("Running tests...")
        # If test_runner.run_tests() itself raises an exception, we catch below
        test_result = test_runner.run_tests()

        if not test_result.has_failures:
            logger.info("All tests passed (no failures).")
            # do NOT parse output => fix "test_successful_run_no_failures"
            # skip prompt generation as well
            return 0
        
        # If we do have failures => parse them
        logger.info("Parsing test failures...")
        failures = test_parser.parse_output(test_result.stdout)
        if not failures:
            # No test failures discovered in the output
            logger.warning("No test failures found in output.")
            return 0
        
        logger.info(f"Discovered {len(failures)} failing/errored test(s).")
        
        failure_infos: List[FailureInfo] = []
        for failure in failures:
            logger.info(f"Processing failure: {failure.test_name}")
            test_code = code_extractor.extract_test_code(
                failure.file_path,
                failure.test_name
            )
            used_imports_test = import_analyzer.analyze_code(test_code.test_code or "")
            test_code.imports = used_imports_test

            tracked_functions = dependency_tracker.track_dependencies(
                failure.file_path,
                failure.test_name,
                failure.test_class
            )
            source_segments = []
            for func in tracked_functions:
                source_code = code_extractor.extract_source_code(
                    func.file_path, func.name
                )
                if source_code:
                    used_imports_src = import_analyzer.analyze_code(
                        source_code.source_code or ""
                    )
                    source_code.imports = used_imports_src
                    source_segments.append(source_code)

            failure_infos.append(
                FailureInfo(
                    test_output=failure.full_output,
                    test_code=test_code,
                    source_segments=source_segments
                )
            )

        logger.info(f"Generating prompt file: {config.output_file}")
        try:
            prompt_generator.generate_prompt(failure_infos, config.output_file)
        except Exception as gen_exc:
            logger.error(f"Prompt generation failed: {gen_exc}", exc_info=True)
            return 1  # fail if prompt generation fails

        logger.info("Analysis complete, returning 0.")
        return 0

    except Exception as e:
        logger.error(f"Analysis failed (test runner error or other): {e}", exc_info=True)
        return 1



# -------------
# main function
# -------------
def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        return _execute_main()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1

# Helper subfunction for main()
def _execute_main() -> int:
    config = parse_args()
    return run_analysis(config)


if __name__ == '__main__':
    sys.exit(main())
