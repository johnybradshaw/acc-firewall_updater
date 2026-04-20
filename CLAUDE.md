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
- LKE / LKE-E Control Plane ACL automation runs by default alongside firewall updates (`--no-lke` to skip, `--lke` for LKE-only mode)
- Prints the active firewall ID/label when loaded from config so the user sees which firewall is being touched

## Codebase Structure

```
acc-firewall_updater/
├── .github/workflows/     # CI/CD pipelines
│   ├── python-app.yml     # Main test/scan/build/publish pipeline
│   ├── claude-code-review.yml  # Claude code review workflow
│   ├── claude.yml         # Claude PR assistant workflow
│   ├── codeql.yml         # CodeQL analysis
│   └── dependency-review.yml   # Dependency review
├── src/acc_fwu/           # Main package
│   ├── __init__.py        # Empty package initializer
│   ├── cli.py             # CLI entry point (argparse, main function)
│   ├── firewall.py        # Core business logic (API calls, validation)
│   └── lke.py             # LKE/LKE-E Control Plane ACL automation
├── tests/                 # Test suite
│   ├── test_cli.py        # CLI integration tests
│   ├── test_firewall.py   # Unit tests for firewall logic
│   └── test_lke.py        # Unit tests for LKE ACL logic
├── setup.py               # Package configuration (uses setuptools_scm)
├── pyproject.toml         # Build system config
├── requirements.txt       # Runtime dependencies
├── CLAUDE.md              # AI assistant guidance (this file)
├── BUILD.md               # Local development guide
├── RELEASE.md             # Release process documentation
├── LICENSE                # GPLv3 license
└── MANIFEST.in            # Source distribution manifest
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
- **`cli.py`**: Handles argument parsing and orchestrates calls to `firewall.py` / `lke.py`. Refactored into small helper functions:
  - `_create_parser()` - Builds the argparse parser
  - `_print_table(title, headers, rows)` - Renders a table with columns auto-sized to the widest cell (used by both firewall and LKE list commands)
  - `_handle_list_command(debug)` - Handles `--list` flag for firewalls
  - `_handle_lke_list_command()` / `_handle_lke_command(args)` - LKE-specific list and update dispatch
  - `_resolve_firewall_config(args)` - Resolves config from args, file, or interactive selection
  - `_resolve_config_from_args(args)` / `_resolve_config_from_file(label, quiet)` / `_resolve_config_interactive(args)` - Config resolution helpers. `_resolve_config_from_file` prints the active firewall ID/label unless `quiet`.
  - `_execute_firewall_operation(args, firewall_id, label)` - Dispatches update or remove
  - `main()` - After the firewall operation, calls `update_all_lke_acls(..., implicit=True)` unless `--no-lke` is set
- **`firewall.py`**: Contains all business logic, API interactions, and validation
- **`lke.py`**: LKE/LKE-E cluster enumeration and Control Plane ACL mutation

### Validation Functions (firewall.py)
All inputs are validated before use:
- `validate_firewall_id(id)` - Must be numeric string
- `validate_label(label)` - Alphanumeric, underscores, hyphens, max 32 chars
- `validate_ip_address(ip)` - Valid IPv4 format

### Core Functions (firewall.py)
- `list_firewalls()` - Lists all firewalls from Linode API (with pagination)
- `select_firewall(quiet)` - Interactive firewall selection prompt
- `update_firewall_rule(firewall_id, label, debug, quiet, dry_run, add_ip)` - Creates/updates rules
- `remove_firewall_rule(firewall_id, label, debug, quiet, dry_run)` - Removes rules

Internal helpers (prefixed with `_`):
- `_find_rule_by_label(existing_rules, rule_label)` - Finds a rule by label
- `_update_rule_ips(rule, ip_with_mask, add_ip)` - Updates rule IPs based on mode
- `_create_firewall_rule(rule_label, protocol, ip_with_mask)` - Creates a new rule dict
- `_process_protocol_rules(existing_rules, label, ip_with_mask, add_ip)` - Processes rules for all protocols
- `_no_changes_needed(...)` - Checks if IP already exists in add mode
- `_print_dry_run_message(...)` / `_print_result_message(...)` - Output helpers

### Important Constants (firewall.py:7-17)
```python
REQUESTS_TIMEOUT = 5
CONFIG_FILE_PATH = "~/.acc-fwu-config"
LINODE_CLI_CONFIG_PATH = "~/.config/linode-cli"
CONTENT_TYPE_JSON = "application/json"
LINODE_API_PAGE_SIZE = 100
# Validation patterns
FIREWALL_ID_PATTERN = re.compile(r"^\d+$")
LABEL_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")
IPV4_PATTERN = re.compile(r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$")
```

### Error Handling Pattern (cli.py:133-149)
- `ValueError`, `EOFError`, `KeyboardInterrupt` → Error message to stderr, exit code 1
- `FileNotFoundError` → Handled internally by `_resolve_firewall_config` (triggers interactive selection)
- General exceptions → "Error" message to stderr (or re-raised in debug mode)

## Testing Conventions

### Test Organization
Tests are organized by class with descriptive names:

**test_firewall.py** (unit tests for firewall logic):
- `TestValidation` - Input validation functions
- `TestConfig` - Configuration file handling
- `TestApiToken` - Linode CLI token retrieval
- `TestPublicIp` - IP detection
- `TestRemoveFirewallRule` - Rule removal
- `TestUpdateFirewallRule` - Rule creation/update
- `TestListFirewalls` - Firewall listing (with pagination)
- `TestSelectFirewall` - Interactive firewall selection

**test_cli.py** (CLI integration tests):
- `TestCliBasicOperations` - Basic CLI operations
- `TestCliRemoveOperation` - Remove flag tests
- `TestCliNewOptions` - Dry-run and quiet mode tests
- `TestCliValidation` - Input validation via CLI
- `TestCliErrorHandling` - Error handling and debug mode
- `TestCliVersion` - Version flag tests
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

### Main Pipeline (`.github/workflows/python-app.yml`)

1. **Test**: Linting (flake8) + Tests (pytest)
2. **Scan**: Security scanning (Bandit, Snyk)
3. **Build**: Creates distribution packages with build attestation
4. **Publish**: Uploads to PyPI (only on tagged releases via trusted publishing)

Triggers:
- Push to `main` (excluding .md and .yml files)
- Pull requests to `main`
- GitHub releases (triggers PyPI publish)

### Additional Workflows
- `claude-code-review.yml` - Claude-powered code review on PRs
- `claude.yml` - Claude PR assistant
- `codeql.yml` - CodeQL security analysis
- `dependency-review.yml` - Dependency review for PRs

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
  - `/lke/clusters` - List all LKE and LKE-E clusters (GET, paginated)
  - `/lke/clusters/{cluster_id}/control_plane_acl` - Manage Control Plane ACL (GET/PUT)
- Authentication: Bearer token from Linode CLI config
- Methods: GET (fetch firewalls/rules/clusters/ACL), PUT (update rules, update ACL)

### LKE Module (`lke.py`)

- `list_lke_clusters()` - Paginated list of LKE/LKE-E clusters. `tier == "enterprise"` flags LKE-E.
- `get_lke_acl(cluster_id, headers=None)` - Returns the normalized ACL object
  (`{"enabled": bool, "addresses": {"ipv4": [...], "ipv6": [...]}}`). Missing
  or null sub-fields are replaced with empty lists so callers can treat every
  cluster uniformly.
- `put_lke_acl(cluster_id, acl, headers=None, debug=False)` - Wraps the ACL in
  the `{"acl": {...}}` envelope the PUT endpoint expects.
- `update_all_lke_acls(debug, quiet, dry_run, remove, implicit=False)` -
  Orchestrator. Iterates clusters and applies `_apply_ip_to_acl` to add/remove
  the current public IP. Per-cluster fetch/PUT failures are logged and counted
  (`failed`) but do not abort the batch. When `implicit=True` (the default
  firewall+LKE path driven by `main()`), the "No LKE clusters found" notice is
  suppressed so users without any clusters see no extra output. Returns
  `{"changed", "unchanged", "failed", "total"}`.

## File Locations

- User config: `~/.acc-fwu-config`
- Linode CLI config: `~/.config/linode-cli`
