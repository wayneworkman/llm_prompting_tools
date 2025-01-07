# python_unittest_tool/main.py

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
    
    # Validate negative number_of_issues -> raise SystemExit
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
    Run the complete test analysis workflow.
    
    Args:
        config: Configuration object
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Initialize components
        test_runner = TestRunner(config.test_dir)
        test_parser = TestOutputParser(config.number_of_issues)
        code_extractor = CodeExtractor()
        dependency_tracker = DependencyTracker(config.project_root)
        prompt_generator = PromptGenerator(config.project_root)
        
        # Run tests and get output
        logger.info("Running tests...")
        test_result = test_runner.run_tests()
        
        if not test_result.has_failures:
            logger.info("All tests passed!")
            return 0
        
        # Parse test failures
        logger.info("Parsing test failures...")
        failures = test_parser.parse_output(test_result.stdout)
        
        if not failures:
            logger.warning("No test failures found in output.")
            return 0
        
        # Process each failure
        failure_infos: List[FailureInfo] = []
        for failure in failures:
            logger.info(f"Processing failure: {failure.test_name}")
            
            # Extract test code
            test_code = code_extractor.extract_test_code(
                failure.file_path,
                failure.test_name
            )
            
            # Track dependencies
            source_segments = []
            tracked_functions = dependency_tracker.track_dependencies(
                failure.file_path,
                failure.test_name,
                failure.test_class
            )
            
            # Extract source code for each dependency
            for func in tracked_functions:
                source_code = code_extractor.extract_source_code(
                    func.file_path,
                    func.name,
                )
                if source_code:
                    source_segments.append(source_code)
            
            # Create failure info
            failure_infos.append(FailureInfo(
                test_output=failure.full_output,
                test_code=test_code,
                source_segments=source_segments
            ))
        
        # Generate prompt
        logger.info(f"Generating prompt file: {config.output_file}")
        prompt_generator.generate_prompt(failure_infos, config.output_file)
        
        logger.info("Analysis complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        return 1


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        config = parse_args()
        return run_analysis(config)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
