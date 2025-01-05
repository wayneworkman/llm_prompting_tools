# dialog_opening

## Overview

`dialog_opening` is a command-line tool that generates a `prompt.txt` file summarizing the contents of a given directory. The intent is to use this tool to "open a dialog" with an LLM by providing relevant context. The `prompt.txt` file can be fed into a Large Language Model (LLM) to ease starting a new dialog session.

## Features

- **Configurable Input Directory:**  
  Specify the directory you want to summarize. This helps you focus on a particular project or subset of files.

- **Configurable Output File:**  
  Choose where to write the generated `prompt.txt`. By default, it writes to `prompt.txt` in the script's directory, but you can override this as needed.

- **Configurable Prompt Instructions File:**  
  - If you **do not** specify `--prompt-instructions`, by default the tool checks for a file named `prompt_instructions.txt` in your current working directory.  
    - If it’s found, it is automatically included.  
    - If it’s **not** found, no error is raised, and no special instructions are included.  
  - If you **do** specify a file with `--prompt-instructions` (i.e. a **non-default** path) but that file does **not** exist, the tool **raises an error** and exits.  

- **Code Fence Handling for All Files:**  
  - If **any** file (Markdown or otherwise) contains triple backticks (```), it is enclosed between **START/END** markers to prevent confusion when pasting into LLM prompts.  
  - Files without triple backticks are enclosed in triple backticks so that the LLM interprets them as code or data blocks.

## Usage

Once installed into your Python environment, you can run:

```
dialog_opening --input-dir /path/to/project --output-file /path/to/output/prompt.txt
```

### Arguments:

- `--input-dir` (optional): The directory to scan. Defaults to the current directory if not specified.
- `--output-file` (optional): The file to write the prompt to. Defaults to `prompt.txt` in the script's directory if not specified.
- `--prompt-instructions` (optional):  
  - Defaults to `prompt_instructions.txt` in the current working directory.  
  - If the default file is **not** found, no error occurs and no instructions are added.  
  - If you explicitly provide a **different** file and it doesn’t exist, the script raises an error.

A `--help` menu is also available:

```
dialog_opening --help
```

## Examples

- **Default usage** (current directory, default instructions if found):  

```
dialog_opening
```

- **Generate a prompt for a specific directory**:  

```
dialog_opening --input-dir /home/user/myproject
```

…and write to a custom file location:

```
dialog_opening --input-dir /home/user/myproject --output-file /home/user/myproject/my_prompt.txt
```

- **Include a custom instructions file**:  

```
dialog_opening --prompt-instructions custom_instructions.txt
```

If `custom_instructions.txt` does not exist, the script will exit with an error.

## Why Use This?

When working with LLMs, providing context can significantly improve the quality of the responses. This tool helps you consolidate your project's structure and content into a single prompt file, making it easy to feed comprehensive context into the LLM.

## Testing

Tests are in the `tests` directory. From the `dialog_opening` directory (or after installing in a virtual environment), you can run them with:

```
python3 -m unittest discover tests
```

## Contributing

Pull requests are welcome! If you add new functionality or modify existing behavior, please include tests. Don’t hesitate to use an LLM to assist in creating or improving tests.

## License

This project is provided under the MIT License.

----

## Installation Instructions

Below is an example of how you can install this tool in a dedicated Python virtual environment.

### MacOS / Linux

1. **Create and activate a new Python virtual environment** (for example, in your home directory):
   ```
   python3 -m venv ~/venv
   source ~/venv/bin/activate
   ```

2. **Make it permanent** (optional).  
   Add this line to your `~/.zshrc` or `~/.bashrc` file:
   ```
   source ~/venv/bin/activate
   ```
   Then reload:
   ```
   source ~/.zshrc
   ```
   or
   ```
   source ~/.bashrc
   ```

3. **Add the virtual environment’s `bin/` directory to your PATH** (so that you can use the tool from any new shell without re-activating):
   ```
   echo 'export PATH="$HOME/venv/bin:$PATH"' >> ~/.zshrc
   ```
   or if using Bash:
   ```
   echo 'export PATH="$HOME/venv/bin:$PATH"' >> ~/.bashrc
   ```

4. **Install** (from within your `dialog_opening` project directory):
   ```
   pip install .
   ```

Now you can call:
```
dialog_opening --help
```
from any directory.

### Windows

1. **Create and activate a new Python virtual environment**:
   ```
   python -m venv C:\path\to\venv
   C:\path\to\venv\Scripts\activate
   ```

2. **(Optional) Make activation permanent**:  
   You can add the `activate` command to your PowerShell profile, or simply run the activation script whenever you open a new shell.

3. **Add the virtual environment’s Scripts directory to PATH** if you want to run commands without manual activation. For instance:
   ```
   $env:Path = "C:\path\to\venv\Scripts;" + $env:Path
   ```
   (You can add the above to your PowerShell profile or system environment variables.)

4. **Install** (from within your `dialog_opening` project directory):
   ```
   pip install .
   ```

Then you can call:
```
dialog_opening --help
```
from any directory (within that virtual environment or if the Scripts folder is on your PATH).
