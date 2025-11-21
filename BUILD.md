# Building acc-fwu Locally

This guide explains how to set up a local development environment for `acc-fwu`.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- git

## Quick Start

```bash
# Clone the repository
git clone https://github.com/johnybradshaw/acc-firewall_updater.git
cd acc-firewall_updater

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dependencies
pip install -e .
pip install -r requirements.txt

# Install development dependencies
pip install pytest flake8
```

## Development Installation

### Option 1: Editable Install (Recommended for Development)

An editable install allows you to modify the source code and see changes immediately without reinstalling:

```bash
pip install -e .
```

### Option 2: Standard Install from Source

```bash
pip install --use-pep517 .
```

## Running Tests

The project uses pytest for testing. All tests are located in the `tests/` directory.

### Run All Tests

```bash
pytest
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run a Specific Test File

```bash
pytest tests/test_firewall.py
pytest tests/test_cli.py
```

### Run a Specific Test Class or Method

```bash
pytest tests/test_firewall.py::TestValidation
pytest tests/test_firewall.py::TestValidation::test_validate_firewall_id_valid
```

### Run Tests with Coverage

```bash
pip install pytest-cov
pytest --cov=acc_fwu --cov-report=html
```

This generates an HTML coverage report in `htmlcov/`.

## Linting

The project uses flake8 for code linting:

```bash
# Run basic linting
flake8 .

# Run with the same settings as CI
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## Building Distribution Packages

To build distribution packages (wheel and source distribution):

```bash
# Install build tools
pip install build

# Build the package
python -m build
```

This creates:
- `dist/acc_fwu-<version>.tar.gz` (source distribution)
- `dist/acc_fwu-<version>-py3-none-any.whl` (wheel)

### Alternative: Using setup.py

```bash
pip install setuptools wheel
python setup.py sdist bdist_wheel
```

## Project Structure

```
acc-firewall_updater/
├── src/
│   └── acc_fwu/
│       ├── __init__.py      # Package initializer
│       ├── cli.py           # CLI entry point
│       └── firewall.py      # Core firewall logic
├── tests/
│   ├── test_cli.py          # CLI tests
│   └── test_firewall.py     # Firewall logic tests
├── setup.py                  # Package setup configuration
├── pyproject.toml            # Build system configuration
├── requirements.txt          # Runtime dependencies
├── README.md                 # Project documentation
├── BUILD.md                  # This file
└── RELEASE.md                # Release process documentation
```

## Testing Without Linode API Access

All tests use mocks to avoid requiring actual Linode API access. The tests mock:

- HTTP requests to the Linode API
- HTTP requests to the IP detection service (api.ipify.org)
- File system operations (configuration files)

This means you can run tests without:
- A Linode account
- A configured Linode CLI
- Internet access

## Common Development Tasks

### Adding a New CLI Option

1. Add the argument in `src/acc_fwu/cli.py` using `parser.add_argument()`
2. Pass the argument to the appropriate function call
3. Update the function signature in `src/acc_fwu/firewall.py` if needed
4. Add tests in `tests/test_cli.py`

### Adding a New Validation Function

1. Add the validation pattern as a constant in `src/acc_fwu/firewall.py`
2. Create the validation function with appropriate error handling
3. Add tests in `tests/test_firewall.py`

### Running the CLI Locally

After installing in development mode:

```bash
# Check version
acc-fwu --version

# Show help
acc-fwu --help

# Dry run (requires Linode CLI configured)
acc-fwu --firewall_id 12345 --label Test --dry-run
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'acc_fwu'"

Make sure you've installed the package in development mode:

```bash
pip install -e .
```

### Tests Fail with Import Errors

Ensure your `PYTHONPATH` includes the `src` directory:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
```

Or run pytest with the src path:

```bash
python -m pytest tests/
```

### Version Shows "0.0.0-dev"

The version is determined by git tags via `setuptools_scm`. If you're working on an untagged commit, the version will show as development. This is expected behavior.

## CI/CD Pipeline

The project uses GitHub Actions for CI/CD. See `.github/workflows/python-app.yml` for details.

The pipeline runs:
1. **Test**: Linting with flake8 and tests with pytest
2. **Scan**: Security scanning with Bandit and Snyk
3. **Build**: Creates distribution packages
4. **Publish**: Publishes to PyPI (only on tagged releases)
