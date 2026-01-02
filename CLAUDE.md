# CLAUDE.md

This file provides guidance for AI assistants working with the `acc-fwu` (Akamai Connected Cloud Firewall Updater) codebase.

## Project Overview

`acc-fwu` is a Python CLI tool that automatically updates Linode/Akamai Connected Cloud firewall rules with the user's current public IP address. It's useful for users with dynamic IPs who need to maintain firewall access.

**Key Features:**
- Auto-detects public IP via api.ipify.org
- Creates TCP, UDP, and ICMP firewall rules
- Persists configuration for repeated use
- Supports dry-run, quiet, and debug modes
- Input validation for security
- Interactive firewall selection (lists available firewalls)
- Add mode for multiple IP addresses (travel use case)

## Codebase Structure

```
acc-firewall_updater/
├── src/acc_fwu/           # Main package
│   ├── __init__.py        # Empty package initializer
│   ├── cli.py             # CLI entry point (argparse, main function)
│   └── firewall.py        # Core business logic (API calls, validation)
├── tests/                 # Test suite
│   ├── test_cli.py        # CLI integration tests
│   └── test_firewall.py   # Unit tests for firewall logic
├── setup.py               # Package configuration (uses setuptools_scm)
├── pyproject.toml         # Build system config
├── requirements.txt       # Runtime dependencies
├── BUILD.md               # Local development guide
└── RELEASE.md             # Release process documentation
```

## Quick Commands

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Run tests with verbose output
pytest -v

# Run linting (same as CI)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Build package
python -m build
```

## Key Code Patterns

### Architecture
- **`cli.py`**: Handles argument parsing and orchestrates calls to `firewall.py`
- **`firewall.py`**: Contains all business logic, API interactions, and validation

### Validation Functions (firewall.py)
All inputs are validated before use:
- `validate_firewall_id(id)` - Must be numeric string
- `validate_label(label)` - Alphanumeric, underscores, hyphens, max 32 chars
- `validate_ip_address(ip)` - Valid IPv4 format

### Core Functions (firewall.py)
- `list_firewalls()` - Lists all firewalls from Linode API
- `select_firewall(quiet)` - Interactive firewall selection prompt
- `update_firewall_rule(firewall_id, label, debug, quiet, dry_run, add_ip)` - Creates/updates rules
- `remove_firewall_rule(firewall_id, label, debug, quiet, dry_run)` - Removes rules

### Important Constants (firewall.py:8-16)
```python
REQUESTS_TIMEOUT = 5
CONFIG_FILE_PATH = "~/.acc-fwu-config"
LINODE_CLI_CONFIG_PATH = "~/.config/linode-cli"
```

### Error Handling Pattern (cli.py:71-121)
- `ValueError` exceptions → "Validation error" message, exit code 1
- `FileNotFoundError` → Configuration guidance message
- General exceptions → "Error" message (or re-raised in debug mode)

## Testing Conventions

### Test Organization
Tests are organized by class with descriptive names:
- `TestValidation` - Input validation functions
- `TestConfig` - Configuration file handling
- `TestApiToken` - Linode CLI token retrieval
- `TestPublicIp` - IP detection
- `TestRemoveFirewallRule` / `TestUpdateFirewallRule` - Core functionality
- `TestListFirewalls` - Firewall listing functionality
- `TestSelectFirewall` - Interactive firewall selection
- `TestCliBasicOperations` - Basic CLI operations
- `TestCliAddFlag` - Add mode (--add flag) tests
- `TestCliListFlag` - List firewalls (--list flag) tests
- `TestCliInteractiveSelection` - Interactive selection tests

### Mocking Strategy
All external dependencies are mocked:
- HTTP requests to Linode API
- HTTP requests to api.ipify.org
- File system operations (config files)
- API token retrieval

Tests do NOT require:
- Internet access
- Linode account/CLI configuration
- Actual firewall access

### Running Specific Tests
```bash
pytest tests/test_firewall.py::TestValidation
pytest tests/test_cli.py::TestCliBasicOperations::test_main_with_firewall_id_and_label
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/python-app.yml`) runs:

1. **Test**: Linting (flake8) + Tests (pytest)
2. **Scan**: Security scanning (Bandit, Snyk)
3. **Build**: Creates distribution packages
4. **Publish**: Uploads to PyPI (only on tagged releases)

Triggers:
- Push to `main` (excluding .md and .yml files)
- Pull requests to `main`
- GitHub releases (triggers PyPI publish)

## Common Development Tasks

### Adding a New CLI Option
1. Add argument in `cli.py` via `parser.add_argument()`
2. Pass to appropriate function in `firewall.py`
3. Update function signature if needed
4. Add tests in `test_cli.py`

### Adding a New Validation Function
1. Add regex pattern as constant in `firewall.py`
2. Create validation function with `ValueError` for invalid input
3. Add tests in `test_firewall.py`

### Making a Release
1. Update changelog in README.md
2. Create annotated git tag: `git tag -a v0.x.x -m "Release v0.x.x"`
3. Push tag: `git push origin v0.x.x`
4. Create GitHub Release (triggers PyPI publish)

## Code Style

- **Max line length**: 127 characters
- **Max complexity**: 10 (flake8)
- **Linting**: flake8 with specific error codes (E9, F63, F7, F82)
- **Versioning**: Semantic versioning via git tags (setuptools_scm)

## Security Considerations

- Config file created with 600 permissions (owner-only)
- API tokens read from Linode CLI config, never stored separately
- All inputs validated before API use
- HTTPS-only API communication

## Dependencies

Runtime:
- `requests` - HTTP client for API calls

Development:
- `pytest` - Testing framework
- `flake8` - Linting
- `build` - Package building

## Troubleshooting

### Import Errors
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
# or
pip install -e .
```

### Version Shows "0.0.0-dev"
This is expected for untagged commits. Version comes from git tags via setuptools_scm.

## API Integration

The tool uses the Linode API v4:
- Base URL: `https://api.linode.com/v4/`
- Endpoints:
  - `/networking/firewalls` - List all firewalls (GET)
  - `/networking/firewalls/{firewall_id}/rules` - Manage rules (GET/PUT)
- Authentication: Bearer token from Linode CLI config
- Methods: GET (fetch firewalls/rules), PUT (update rules)

## File Locations

- User config: `~/.acc-fwu-config`
- Linode CLI config: `~/.config/linode-cli`
