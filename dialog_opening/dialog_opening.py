#!/usr/bin/env python3
# dialog_opening.py

import os
import argparse
import sys
from lib.prompt_generation import generate_prompt

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Generate a prompt file from a directory's contents, "
                    "only excluding items matched by .gitignore and excluding the .git directory."
    )
    parser.add_argument(
        "--input-dir",
        default=".",
        help="The directory to read files from. Defaults to current directory."
    )
    parser.add_argument(
        "--output-file",
        default=os.path.join(script_dir, "prompt.txt"),
        help="The file to write the prompt to. Defaults to 'prompt.txt' in the script's directory."
    )
    args = parser.parse_args()

    # Pre-check directory existence
    if not os.path.isdir(args.input_dir):
        print("Directory not found")
        sys.exit(1)

    # Pre-check write permissions to output file
    try:
        with open(args.output_file, 'w'):
            pass
    except PermissionError:
        print("No write permissions")
        sys.exit(1)

    # If directory exists and we can write to output, run generate_prompt
    try:
        generate_prompt(args.input_dir, args.output_file)
        print(f"{args.output_file} generated successfully.")
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)
    except PermissionError as e:
        print(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
