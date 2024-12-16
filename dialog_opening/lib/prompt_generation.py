# lib/prompt_generation.py (place in ./lib/prompt_generation.py)

import os
from lib.listing import recursive_list
from lib.gitignore_utils import load_gitignore_patterns, should_include_file

def generate_prompt(input_dir, output_file):
    # Check directory existence
    if not os.path.isdir(input_dir):
        raise FileNotFoundError("Directory not found")

    # Check write permission
    try:
        with open(output_file, 'w'):
            pass
    except PermissionError:
        raise PermissionError("No write permissions")

    patterns = load_gitignore_patterns(input_dir)

    special_instructions_path = os.path.join(input_dir, "SPECIAL_PROMPT_INSTRUCTIONS.txt")
    special_instructions = ""
    if os.path.isfile(special_instructions_path):
        with open(special_instructions_path, 'r', encoding='utf-8', errors='replace') as f:
            special_instructions = f.read().strip()

    listing_lines = recursive_list(input_dir, input_dir, patterns)

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
        if full_path and should_include_file(full_path, input_dir, patterns):
            # Exclude the output file itself
            if os.path.abspath(full_path) == os.path.abspath(output_file):
                continue
            included_files.append(full_path)

    # New approach: Group files so that markdown files with code fences come first.
    with_code_fences = []
    without_code_fences = []
    non_markdown = []

    for fpath in included_files:
        rel_name = os.path.relpath(fpath, input_dir)
        with open(fpath, 'rb') as fb:
            content_bytes = fb.read()
        content = content_bytes.decode('utf-8', 'replace')

        if is_markdown_file(rel_name):
            if has_code_fences(content):
                with_code_fences.append((rel_name, content))
            else:
                without_code_fences.append((rel_name, content))
        else:
            non_markdown.append((rel_name, content))

    # Print files in the order: markdown with fences, markdown without fences, non-markdown
    file_sections = with_code_fences + without_code_fences + non_markdown

    with open(output_file, 'w', encoding='utf-8', errors='replace') as out:
        if special_instructions:
            out.write(special_instructions + "\n\n")

        out.write("Below is the directory structure:\n```\n")
        for line in listing_lines:
            out.write(line + "\n")
        out.write("```\n\n")

        out.write("Below are the file contents:\n\n")

        for (rel_name, content) in file_sections:
            out.write(rel_name + "\n")
            if is_markdown_file(rel_name):
                if has_code_fences(content):
                    out.write("START OF MARKDOWN FILE WITH CODE FENCES\n")
                    out.write(content)
                    out.write("\nEND OF MARKDOWN FILE WITH CODE FENCES\n\n")
                else:
                    out.write("```\n")
                    out.write(content)
                    out.write("\n```\n\n")
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
