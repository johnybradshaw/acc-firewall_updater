# acc-firewall_updater

A tool to automatically update the [Akamai Connected Cloud (ACC) / Linode](https://www.akamai.com/cloud) firewall rules to allow your IP.

[![Test, Scan, Build, & Publish](https://github.com/johnybradshaw/acc-firewall_updater/actions/workflows/python-app.yml/badge.svg)](https://github.com/johnybradshaw/acc-firewall_updater/actions/workflows/python-app.yml)
[![PyPI version](https://badge.fury.io/py/acc-fwu.svg)](https://badge.fury.io/py/acc-fwu)

## Description

`acc-fwu` is a command-line tool to automatically update [Linode](https://www.linode.com)/ACC firewall rules with your current IP address. This is particularly useful for dynamically updating firewall rules to allow access from changing IP addresses, like when you visit the gym or you're sat in an airport.

## Features

- Automatically detects your current public IP address
- Creates firewall rules for TCP, UDP, and ICMP protocols
- Saves configuration for easy subsequent usage
- Supports dry-run mode to preview changes
- Quiet mode for cron jobs and automation
- Debug mode for troubleshooting
- Input validation for security
- Secure configuration file storage (owner-only permissions)
- **Interactive firewall selection** - List and choose from available firewalls
- **Add mode** - Accumulate multiple IP addresses (ideal for traveling)

## Prerequisites

- Python 3.6 or higher
- [Linode CLI](https://www.linode.com/docs/products/tools/cli/get-started/) configured with an API token
- A Linode/ACC firewall ID

## Installation

You can install the package via `pip` or `pipx`:

```bash
pipx install acc-fwu
```

Alternatively, you can install it directly from the source:

```bash
git clone https://github.com/johnybradshaw/acc-firewall_updater.git
cd acc-firewall_updater
pip install --use-pep517 .
```

For development installation, see [BUILD.md](BUILD.md).

## Usage

### First-time Setup

The first time you use `acc-fwu`, you'll need to provide your Linode/ACC Firewall ID and *optionally* the label for the rule you want to create or update:

```bash
acc-fwu --firewall_id <FIREWALL_ID> --label <RULE_LABEL>
```

For example:

```bash
acc-fwu --firewall_id 123456 --label "Allow-My-Current-IP"
```

This command will do two things:

1. It will create or update the firewall rule with your current public IP address.
2. It will save the `firewall_id` and `label` to a configuration file `(~/.acc-fwu-config)` for future use.

### Subsequent Usage

After the initial setup, you can simply run `acc-fwu` without needing to provide the `firewall_id` and `label` again:

```bash
acc-fwu
```

This will:

1. Load the saved `firewall_id` and `label` from the configuration file.
2. Update the firewall rule with your current public IP address.

### Command-Line Options

```
usage: acc-fwu [-h] [--firewall_id FIREWALL_ID] [--label LABEL] [-d] [-r] [-a] [-l] [-q] [--dry-run] [-v]

Create, update, or remove Akamai Connected Cloud (Linode) firewall rules with your current IP address.

options:
  -h, --help            show this help message and exit
  --firewall_id FIREWALL_ID
                        The numeric ID of the Linode firewall.
  --label LABEL         Label for the firewall rule (alphanumeric, underscores, hyphens, max 32 chars).
  -d, --debug           Enable debug mode to show existing rules data.
  -r, --remove          Remove the specified rules from the firewall.
  -a, --add             Add IP to existing rules instead of replacing (useful for multiple locations).
  -l, --list            List available firewalls and exit.
  -q, --quiet           Suppress output messages (useful for cron/scripting).
  --dry-run             Show what would be done without making any changes.
  -v, --version         show program's version number and exit

Example: acc-fwu --firewall_id 12345 --label MyIP
```

### Examples

**Preview changes without applying them:**

```bash
acc-fwu --firewall_id 123456 --label "My-IP" --dry-run
```

**Run silently (for cron jobs):**

```bash
acc-fwu --quiet  # Requires existing config file
```

**Remove firewall rules:**

```bash
acc-fwu --remove
```

**Debug mode (shows existing rules):**

```bash
acc-fwu --debug
```

**Check version:**

```bash
acc-fwu --version
```

**List available firewalls:**

```bash
acc-fwu --list
```

**Add IP without replacing existing ones (great for traveling):**

```bash
acc-fwu --add
```

**First-time setup with interactive firewall selection:**

```bash
# If no firewall_id is provided and no config exists,
# you'll be prompted to select from available firewalls
acc-fwu
```

### Multi-Location Usage (Add Mode)

If you frequently travel and need to access your servers from multiple locations, use the `--add` flag:

```bash
# From home
acc-fwu --add

# Later, from a coffee shop
acc-fwu --add

# Later, from the airport
acc-fwu --add
```

Each location's IP address will be added to your firewall rules, allowing access from all locations. Without `--add`, your IP would be replaced each time.

To start fresh and remove all accumulated IPs:

```bash
acc-fwu --remove
acc-fwu  # Creates new rules with only your current IP
```

### Cron Job Example

To automatically update your firewall rules every hour:

```bash
# Update firewall rules every hour
0 * * * * /usr/local/bin/acc-fwu --quiet
```

**Important**: Before using `--quiet` mode, you must have a valid configuration file (`~/.acc-fwu-config`) with your `firewall_id` and `label`. Interactive firewall selection is not available in quiet mode. Run `acc-fwu` interactively first to set up your configuration.

## Configuration File

The `acc-fwu` tool saves the `firewall_id` and `label` in a configuration file located at `~/.acc-fwu-config`. This file is:

- Automatically managed by the tool
- Created with secure permissions (readable only by owner)
- Uses standard INI format

You generally won't need to edit it manually.

## Security

- **Input Validation**: All inputs (firewall ID, labels, IP addresses) are validated before use
- **Secure Config Storage**: Configuration file is created with `600` permissions (owner read/write only)
- **No Credential Storage**: API tokens are read from the Linode CLI configuration, not stored separately
- **HTTPS Only**: All API communications use HTTPS

## Development

See [BUILD.md](BUILD.md) for local development and testing instructions.

See [RELEASE.md](RELEASE.md) for information on creating releases.

## License

This project is licensed under the GNU General Public License v3 (GPLv3) - see the [LICENSE](LICENSE) file for details.

## Summary of Changes

### 2026-01-05 - v0.2.1

- **Bug Fixes**:
  - Fixed `select_firewall()` hanging in quiet mode - now raises an error immediately with guidance to configure firewall_id first
  - Quiet mode (`--quiet`) now properly fails fast in non-interactive environments (e.g., cron jobs) when no configuration exists

### 2026-01-02 - v0.2.0

- **New Features**:
  - Added `--list` / `-l` flag to list available firewalls from your Linode account
  - Added `--add` / `-a` flag to append IP addresses to existing rules instead of replacing (useful when traveling between multiple locations)
  - Added interactive firewall selection when no firewall_id is configured
- **Improvements**:
  - When running without a config file, the tool now prompts you to select from available firewalls
  - Better handling of multiple IP addresses per rule

### 2025-11-21 - v0.1.5

- **New Features**:
  - Added `--version` / `-v` flag to display installed version
  - Added `--dry-run` flag to preview changes without applying them
  - Added `--quiet` / `-q` flag to suppress output for cron/scripting
- **Security Improvements**:
  - Added input validation for firewall_id (numeric only)
  - Added input validation for labels (alphanumeric, underscores, hyphens, max 32 chars)
  - Added IP address validation
  - Configuration file now created with secure permissions (600)
- **Usability Improvements**:
  - Proper exit codes (0 for success, 1 for errors)
  - Error messages now output to stderr
  - Improved help text with usage examples

### 2025-06-03 - v0.1.4

- **Security Fixes**: Updated Python dependencies to resolve security vulnerabilities.

### 2024-10-01 - v0.1.3

- **Show IP Address**: Now shows the current public IP address when it is updated.

### 2024-08-20 - v0.1.2

- **Fixes**: Fixed issue with updating the firewall rule.

### 2024-08-18 - v0.1.1

- **Remove Firewall Rules**: Instructions on how to remove the firewall rule.

### 2024-08-17 - v0.1.0

- **First-time Setup**: Instructions on how to set the `firewall_id` and `label` the first time you use the tool.
- **Subsequent Usage**: Information about running the tool without additional arguments after the initial setup.
- **Updating the Configuration**: Guidance on how to change the stored `firewall_id` and `label` if needed.
- **Configuration File**: Brief explanation of the config file and its location.
