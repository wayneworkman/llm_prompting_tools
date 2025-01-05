# lib/prompt_generation.py (place in ./lib/prompt_generation.py)

import os
from lib.listing import recursive_list
from lib.gitignore_utils import load_gitignore_spec, should_include_file
from lib.detect_file_type import is_binary_file

def generate_prompt(input_dir, output_file, prompt_instructions=None):
    # Check directory existence
    if not os.path.isdir(input_dir):
        raise FileNotFoundError("Directory not found")

    # Check write permission
    try:
        with open(output_file, 'w'):
            pass
    except PermissionError:
        raise PermissionError("No write permissions")

    # Load the .gitignore as a PathSpec
    gitignore_spec = load_gitignore_spec(input_dir)

    # Build the directory listing lines, respecting the .gitignore
    listing_lines = recursive_list(input_dir, input_dir, gitignore_spec)

    # Collect included files
    included_files = []
    for line in listing_lines:
        line = line.strip()
        if not line or line.endswith(':') or line.startswith("total "):
            continue
        parts = line.split()
        if len(parts) < 9:
            continue
        filename = parts[-1]
        full_path = find_file_path(input_dir, filename)
        if full_path and should_include_file(full_path, input_dir, gitignore_spec):
            # Exclude the output file itself
            if os.path.abspath(full_path) == os.path.abspath(output_file):
                continue
            included_files.append(full_path)

    # We keep separate lists to maintain the original ordering:
    #   1) markdown with fences
    #   2) markdown without fences
    #   3) non-markdown
    # Also skip content for truly binary files.
    with_code_fences = []
    without_code_fences = []
    non_markdown = []

    for fpath in included_files:
        rel_name = os.path.relpath(fpath, input_dir)
        if is_binary_file(fpath):
            # We'll enclose the file name in the final output but exclude contents
            if is_markdown_file(rel_name):
                with_code_fences.append((rel_name, None, True))
            else:
                non_markdown.append((rel_name, None, True))
            continue

        # If we got here, it's text, so let's read the file content
        with open(fpath, 'rb') as fb:
            content_bytes = fb.read()
        content = content_bytes.decode('utf-8', 'replace')

        # Now check if it's markdown and if it has code fences
        if is_markdown_file(rel_name):
            if has_code_fences(content):
                with_code_fences.append((rel_name, content, False))
            else:
                without_code_fences.append((rel_name, content, False))
        else:
            non_markdown.append((rel_name, content, False))

    file_sections = with_code_fences + without_code_fences + non_markdown

    # Write the prompt
    with open(output_file, 'w', encoding='utf-8', errors='replace') as out:
        # If there are custom instructions, include them
        if prompt_instructions:
            out.write(prompt_instructions + "\n\n")

        out.write("Below is the directory structure:\n```\n")
        for line in listing_lines:
            out.write(line + "\n")
        out.write("```\n\n")

        out.write("Below are the file contents:\n\n")

        for (rel_name, content, is_binary) in file_sections:
            out.write(rel_name + "\n")
            if is_binary:
                out.write("```BINARY FILE CONTENTS EXCLUDED```\n\n")
            else:
                if has_code_fences(content):
                    out.write("START OF FILE WITH CODE FENCES\n")
                    out.write(content)
                    out.write("\nEND OF FILE WITH CODE FENCES\n\n")
                else:
                    out.write("```\n")
                    out.write(content)
                    out.write("\n```\n\n")


def find_file_path(root, filename):
    for dirpath, dirnames, filenames in os.walk(root):
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None

def is_markdown_file(fname):
    return fname.lower().endswith(".md")

def has_code_fences(content):
    return "```" in content
