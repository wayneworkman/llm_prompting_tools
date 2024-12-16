# dialog_opening.py

## Overview

`dialog_opening.py` is a utility script that generates a `prompt.txt` file summarizing the contents of a given directory. The intent is to use this script to "open a dialog" with an LLM. The prompt.txt file can be fed into a Large Language Model (LLM) to ease starting a new dialog session with an LLM.

## Features

- **Configurable Input Directory:**  
  Specify the directory you want to summarize. This helps you focus on a particular project or subset of files.

- **Configurable Output File:**  
  Choose where to write the generated `prompt.txt`. By default, it writes to `prompt.txt` in the script's directory, but you can override this as needed.

- **Special Prompt Instructions:**  
  The script includes a set of instructions at the beginning of the prompt, guiding the LLM to analyze the provided files for interoperability, potential issues, and suspicious code patterns like demos or stubs.

- **Markdown & Non-Markdown Handling:**  
  - Markdown files containing code fences are enclosed in START/END markers to prevent confusion with the prompt formatting.  
  - Markdown files without triple backticks and all other files are enclosed in triple backticks, ensuring the LLM sees them as code or data blocks.

## Usage

Run `dialog_opening.py` from the command line:

```bash
./dialog_opening.py --input-dir /path/to/project --output-file /path/to/output/prompt.txt
```

**Arguments:**

- `--input-dir` (optional): The directory to scan. Defaults to the current directory if not specified.
- `--output-file` (optional): The file to write the prompt to. Defaults to `prompt.txt` in the script's directory if not specified.

## Examples

Generate a prompt for the current directory and write to `prompt.txt`:

```bash
./dialog_opening.py
```

Generate a prompt for a specific project directory and save to a custom location:

```bash
./dialog_opening.py --input-dir /home/user/myproject --output-file /home/user/myproject/my_prompt.txt
```

## Why Use This?

When working with LLMs, providing context can significantly improve the quality of the responses. This tool helps you consolidate your project's structure and content into a single prompt file, making it easy to feed comprehensive context into the LLM. This leads to better insights, feedback, and suggestions for improvement.

## Testing

Tests are in the tests directory. From the dialog_opening directory, you can run them with:

```bash
python3 -m unittest discover tests
```

Ensure that you have appropriate mocking and that your environment is set up as described in the test documentation.

## Contributing

Pull requests are welcome! If you add new functionality or modify existing behavior, please include tests. Don’t hesitate to use an LLM to assist in creating or improving tests.

## License

This project is provided under the MIT License.
