#!/usr/bin/env python3
# __init__.py

import os
import argparse
import sys
from importlib.metadata import version
from lib.prompt_generation import generate_prompt

def main():
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
        default="prompt.txt",
        help="The file to write the prompt to. Defaults to 'prompt.txt' in the current working directory."
    )
    parser.add_argument(
        "--prompt-instructions",
        default="prompt_instructions.txt",
        help=(
            "Path to a file containing additional prompt instructions. "
            "Defaults to 'prompt_instructions.txt' in the current directory. "
            "If it's the default and not found, the file is simply not included. "
            "If you specify a different file and it's not found, the script exits with an error."
        )
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"dialog_opening {version('dialog_opening')}",
        help="Show program's version number and exit."
    )

    args = parser.parse_args()

    # If we got here, --version wasn't used, so proceed with normal operation

    # Ensure input directory exists
    if not os.path.isdir(args.input_dir):
        print("Directory not found")
        sys.exit(1)

    # The user either gave --output-file, or we defaulted to "prompt.txt" in the current dir.
    output_path = os.path.join(os.getcwd(), args.output_file) if not os.path.isabs(args.output_file) \
        else args.output_file

    # Pre-check that we can open that file for writing
    try:
        with open(output_path, 'w'):
            pass
    except (PermissionError, IsADirectoryError):
        print("No write permissions")
        sys.exit(1)

    # Resolve the path to the instructions file in the current working dir
    instructions_path = os.path.join(os.getcwd(), args.prompt_instructions)

    default_instructions_file = "prompt_instructions.txt"
    instructions_text = ""

    if args.prompt_instructions == default_instructions_file:
        # Only read if it actually exists
        if os.path.isfile(instructions_path):
            try:
                with open(instructions_path, 'r', encoding='utf-8', errors='replace') as f:
                    instructions_text = f.read().strip()
            except Exception:
                # If there's any error reading, treat it as empty
                instructions_text = ""
    else:
        # The user gave a custom file
        if not os.path.isfile(instructions_path):
            print("Error: specified instructions file not found")
            sys.exit(1)
        else:
            try:
                with open(instructions_path, 'r', encoding='utf-8', errors='replace') as f:
                    instructions_text = f.read().strip()
            except Exception:
                print("Error: could not read the specified instructions file")
                sys.exit(1)

    # Now call generate_prompt
    try:
        generate_prompt(
            input_dir=args.input_dir,
            output_file=output_path,
            prompt_instructions=instructions_text
        )
        print(f"{output_path} generated successfully.")
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)
    except PermissionError as e:
        print(str(e))
        sys.exit(1)