# python_unittest_tool

## Overview

`python_unittest_tool` is a command-line utility designed to:
- Execute your Python unittests and identify failing tests
- Automatically extract relevant test code, source code, dependencies, and imports
- Aggregate all necessary pieces into a single `prompt.txt` (or another file of your choosing) that you can feed to an LLM for debugging or analysis

## Features

- **Automated Test Execution**  
  Runs your `unittest` suite and gathers failures directly from test output.

- **Minimal Code Extraction**  
  Only the code needed to understand failures is collected. This helps reduce token usage and noise when using large language models.

- **Dependency Tracking**  
  Recursively follows function dependencies across files, preserving any relevant imports, class definitions, and more.

- **Customizable**  
  - Choose which test directory to scan (defaults to `tests`)
  - Limit how many failures you include with `--number-of-issues`
  - Override default file locations and instructions
  - **Check version** with `--version`

## Usage

Once installed, run `python_unittest_tool` with various arguments. For example:

```
python_unittest_tool --project-root . --test-dir tests --number-of-issues 1 --output-file prompt.txt
```

- To see the tool’s version and exit:

```
python_unittest_tool --version
```

### Arguments

- `--version`: Show the program's version number (from the pyproject.toml) and exit.
- `--project-root`: Root directory of your project (default: current directory).
- `--test-dir`: Directory containing tests (default: `tests`).
- `--number-of-issues`: Maximum number of failing tests to include (0 means all, default: 1).
- `--output-file`: Where to write the compiled prompt (default: `prompt.txt`).

For more help, try:

```
python_unittest_tool --help
```

## Examples

- **Run tests in the default directory**:
  ```
  python_unittest_tool
  ```

- **Specify a custom project root** (e.g., a large monorepo) and custom test directory:
  ```
  python_unittest_tool --project-root /home/youruser/myproject --test-dir test_folder
  ```

- **Include all discovered failures**:
  ```
  python_unittest_tool --number-of-issues 0
  ```

- **Check the version and exit**:
  ```
  python_unittest_tool --version
  ```

## Why Use This?

Writing prompts for LLMs can be tedious, especially when you only need specific failing tests and minimal relevant code. This tool helps you avoid copy-pasting large code blocks, letting you focus on problem-solving rather than manual triage and formatting.

## Testing

Tests are located under the `tests` directory. To execute them:

```
python -m unittest discover tests
```

(You can also run from the project root by specifying `--test-dir tests` if you’ve installed this package in a virtual environment.)

## Contributing

Pull requests are welcome! Feel free to open issues or submit bug fixes, new features, or other improvements. If you modify existing functionality or add new features, please include or update the related tests.

## License

This project is distributed under the [MIT License](https://opensource.org/licenses/MIT). Check the `LICENSE` file for details.

----

## Installation Instructions

Below is an example of how you can install this tool in a dedicated Python virtual environment.

### MacOS / Linux

1. **Create and activate a new Python virtual environment** (for example, in your home directory):
   ```
   python3 -m venv ~/venv
   source ~/venv/bin/activate
   ```

2. **(Optional) Make it permanent.**  
   Add this line to your shell’s config (e.g. `~/.zshrc` or `~/.bashrc`):
   ```
   source ~/venv/bin/activate
   ```

3. **Add the virtual environment’s `bin/` directory to your PATH** (so you can run the tool without manually activating):
   ```
   echo 'export PATH="$HOME/venv/bin:$PATH"' >> ~/.zshrc
   ```
   or for Bash:
   ```
   echo 'export PATH="$HOME/venv/bin:$PATH"' >> ~/.bashrc
   ```

4. **Install** (from within your `python_unittest_tool` project directory):
   ```
   pip install .
   ```

Now you can run:
```
python_unittest_tool --help
```
from any directory.

### Windows

1. **Create and activate a new Python virtual environment**:
   ```
   python -m venv C:\path\to\venv
   C:\path\to\venv\Scripts\activate
   ```

2. **(Optional) Make activation permanent**:  
   Add the `activate` command to your PowerShell profile or run it each new session.

3. **Add the virtual environment’s Scripts folder to your PATH** (so you can call the tool without manual activation):
   ```
   $env:Path = "C:\path\to\venv\Scripts;" + $env:Path
   ```

4. **Install** (from within your `python_unittest_tool` project directory):
   ```
   pip install .
   ```

Then you can run:
```
python_unittest_tool --help
```
from any directory (as long as the environment is active or the Scripts folder is on your PATH).
