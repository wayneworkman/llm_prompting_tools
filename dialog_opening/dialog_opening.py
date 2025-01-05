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
    parser.add_argument(
        "--prompt-instructions",
        default="prompt_instructions.txt",
        help=(
        "Path to a file containing additional prompt instructions. "
        "Defaults to 'prompt_instructions.txt' in the current directory. "
        "If it’s the default and not found, no error is raised (the file is simply not included). "
        "If you specify a different file and it’s not found, the script exits with an error."
    )
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
    except (PermissionError, IsADirectoryError):
        print("No write permissions")
        sys.exit(1)

    # Resolve the path to the instructions file in current working dir
    instructions_path = os.path.join(os.getcwd(), args.prompt_instructions)

    # Distinguish between default vs. user-specified instructions file
    default_instructions_file = "prompt_instructions.txt"
    instructions_text = ""

    if args.prompt_instructions == default_instructions_file:
        # User did NOT explicitly specify a different file, so only read if it exists
        if os.path.isfile(instructions_path):
            try:
                with open(instructions_path, 'r', encoding='utf-8', errors='replace') as f:
                    instructions_text = f.read().strip()
            except Exception:
                # If there's any error reading, treat it as empty
                instructions_text = ""
    else:
        # User explicitly gave a different file. If it doesn't exist, raise an error
        if not os.path.isfile(instructions_path):
            print("Error: specified instructions file not found")
            sys.exit(1)
        else:
            # Read the custom file
            try:
                with open(instructions_path, 'r', encoding='utf-8', errors='replace') as f:
                    instructions_text = f.read().strip()
            except Exception:
                print("Error: could not read the specified instructions file")
                sys.exit(1)

    # If directory exists and we can write to output, run generate_prompt
    try:
        generate_prompt(
            input_dir=args.input_dir,
            output_file=args.output_file,
            prompt_instructions=instructions_text
        )
        print(f"{args.output_file} generated successfully.")
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)
    except PermissionError as e:
        print(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
