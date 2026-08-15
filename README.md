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
- **LKE Control Plane ACL automation** - Every run also syncs your public IP into every LKE and LKE-E cluster's Control Plane ACL (opt-out with `--no-lke`; use `--lke` for LKE-only mode; enable a disabled ACL with `--lke-enable-acl`)
- **Managed Database allow_list automation** - Every run also syncs your public IP into every MySQL/PostgreSQL Managed Database `allow_list` (opt-out with `--no-database`; use `--database` for database-only mode; lock down open ranges with `--db-enable-firewall`)
- **Active firewall indicator** - When the config file is used, `acc-fwu` prints the firewall ID and label it's operating on

## Prerequisites

- Python 3.14 or higher
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
2. Print the active firewall (for example `Using saved firewall: ID 123456, label 'My-IP' (from ~/.acc-fwu-config)`).
3. Update the firewall rule with your current public IP address.
4. Sync your current public IP into every LKE / LKE-E Control Plane ACL in your account. Pass `--no-lke` to skip this step.
5. Sync your current public IP into every Managed Database (MySQL/PostgreSQL) `allow_list` in your account. Pass `--no-database` to skip this step.

### Command-Line Options

```
usage: acc-fwu [-h] [--firewall_id FIREWALL_ID] [--label LABEL] [-d] [-r] [-a] [-l] [--lke] [--no-lke] [--lke-enable-acl] [--database] [--no-database] [--db-enable-firewall] [-q] [--dry-run] [-v]

Create, update, or remove Akamai Connected Cloud (Linode) firewall rules with your current IP address.

options:
  -h, --help            show this help message and exit
  --firewall_id FIREWALL_ID
                        The numeric ID of the Linode firewall.
  --label LABEL         Label for the firewall rule (alphanumeric, underscores, hyphens, max 32 chars).
  -d, --debug           Enable debug mode to show existing rules data.
  -r, --remove          Remove the specified rules from the firewall.
  -a, --add             Add IP to existing rules instead of replacing (useful for multiple locations).
  -l, --list            List available firewalls (or LKE clusters with --lke, or managed databases with --database) and exit.
  --lke                 Target LKE/LKE-E Control Plane ACLs only; skip firewall rules.
                        Adds (or removes with -r) your current public IP to every cluster's ACL.
  --no-lke              Skip the default LKE/LKE-E Control Plane ACL update.
                        By default, acc-fwu updates firewall rules, LKE ACLs, and managed database allow_lists.
  --lke-enable-acl      When updating LKE/LKE-E clusters, also enable the Control Plane ACL
                        (firewall) if it is currently disabled, so the added IP is enforced.
                        No effect with -r/--remove.
  --database            Target managed database allow_lists only; skip firewall rules.
                        Adds (or removes with -r) your current public IP to every managed database's allow_list.
  --no-database         Skip the default managed database allow_list update.
                        By default, acc-fwu updates firewall rules, LKE ACLs, and managed database allow_lists.
  --db-enable-firewall  When updating managed databases, remove open ranges (0.0.0.0/0, ::/0)
                        from the allow_list so only explicitly-allowed IPs can connect.
                        No effect with -r/--remove.
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

### LKE / LKE-E Control Plane ACLs

`acc-fwu` automates [Control Plane ACL](https://techdocs.akamai.com/linode-api/reference/put-lke-cluster-acl) updates for every LKE and LKE-Enterprise (LKE-E) cluster in your account. For each cluster it fetches the current ACL, then appends (or removes) your public IP — preserving the `enabled` state and any existing IPv4/IPv6 entries.

**Default behaviour (since v0.3.1):** every firewall update also syncs your IP into each cluster's Control Plane ACL. Accounts with no clusters see no extra output. Pass `--no-lke` to skip it, or `--lke` for LKE-only mode.

**List all LKE / LKE-E clusters:**

```bash
acc-fwu --lke --list
```

**Skip the LKE step while still updating firewall rules:**

```bash
acc-fwu --no-lke
```

**LKE-only mode (skip firewall rule updates entirely):**

```bash
acc-fwu --lke
```

**Preview changes:**

```bash
acc-fwu --lke --dry-run
```

**Remove your current IP from every cluster's ACL:**

```bash
acc-fwu --lke --remove
```

**Enable the Control Plane ACL (firewall) as you add your IP:**

By default the `enabled` state is preserved, so an IP added to a *disabled* ACL is stored but not enforced. Pass `--lke-enable-acl` to switch the firewall on for any cluster whose ACL is currently disabled, so the added IP takes effect immediately:

```bash
acc-fwu --lke --lke-enable-acl
```

This works in the default combined run too (e.g. `acc-fwu --lke-enable-acl`). It has no effect with `-r/--remove` — enabling a firewall while withdrawing your own IP would be contradictory.

**Run silently in a cron job:**

```bash
# Refresh firewall rules + LKE ACLs every 15 minutes
*/15 * * * * /usr/local/bin/acc-fwu --quiet

# Or, LKE only
*/15 * * * * /usr/local/bin/acc-fwu --lke --quiet
```

Clusters whose ACL is disabled will still have the address stored, but `acc-fwu` prints a warning — the entry will not be enforced until you enable the ACL. Failures on individual clusters are logged and counted in the final summary but do not abort the run.

### Managed Database `allow_list`

`acc-fwu` automates [`allow_list`](https://techdocs.akamai.com/linode-api/reference/put-databases-mysql-instance) updates for every Linode Managed Database (MySQL and PostgreSQL) in your account. For each database it appends (or removes) your public IP, preserving any other entries already present.

**Default behaviour:** every firewall update also syncs your IP into each managed database's `allow_list`. Accounts with no databases see no extra output. Pass `--no-database` to skip it, or `--database` for database-only mode.

**List all managed databases:**

```bash
acc-fwu --database --list
```

**Skip the database step while still updating firewall rules:**

```bash
acc-fwu --no-database
```

**Database-only mode (skip firewall rule updates entirely):**

```bash
acc-fwu --database
```

**Preview changes:**

```bash
acc-fwu --database --dry-run
```

**Remove your current IP from every database's allow_list:**

```bash
acc-fwu --database --remove
```

**Lock down the firewall as you add your IP:**

Managed databases have no separate firewall on/off toggle — the `allow_list` *is* the firewall, and an entry of `0.0.0.0/0` (or `::/0`) leaves it open to the whole internet. Pass `--db-enable-firewall` to strip those open ranges while adding your IP, so only explicitly-allowed addresses can connect:

```bash
acc-fwu --database --db-enable-firewall
```

This works in the default combined run too (e.g. `acc-fwu --db-enable-firewall`). It has no effect with `-r/--remove`. Because your IP is always added before the open ranges are removed, the `allow_list` is never left empty (which would block all connections).

Databases on engines other than `mysql` or `postgresql` are reported as a per-database skip. Failures on individual databases are logged and counted in the final summary but do not abort the run.

### Cron Job Example

To automatically update your firewall rules (along with LKE / LKE-E Control Plane ACLs and Managed Database `allow_list`s) every hour:

```bash
# Update firewall rules + LKE ACLs + database allow_lists every hour
0 * * * * /usr/local/bin/acc-fwu --quiet

# Firewall only (skip LKE and database steps)
0 * * * * /usr/local/bin/acc-fwu --quiet --no-lke --no-database
```

**Important**: Before using `--quiet` mode, you must have a valid configuration file (`~/.acc-fwu-config`) with your `firewall_id` and `label`. Interactive firewall selection is not available in quiet mode. Run `acc-fwu` interactively first to set up your configuration.

### Exit Codes

`acc-fwu` reports its outcome through the exit code, so cron and scripts can detect problems:

- `0` — success (including no-op runs where everything was already up to date)
- `1` — fatal error (invalid input, missing configuration, API/authentication failure)
- `2` — the run completed, but one or more targets failed to update (e.g. a PUT to one LKE cluster or database errored while the others succeeded)

Failures are always printed to `stderr`, even with `--quiet` — quiet mode silences informational output, not diagnostics — so failed cron runs leave a trail in your logs or cron mail. Expected skips (unsupported database engines, VPC-attached databases) are reported on `stderr` as `skipped` in the summary, respect `--quiet`, and do not affect the exit code.

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

The project uses multiple GitHub Actions workflows for quality assurance:
- **Test, Scan, Build, & Publish** - Main CI/CD pipeline (lint, test, security scan, build, PyPI publish)
- **CodeQL Analysis** - Automated code security scanning
- **Dependency Review** - Reviews dependency changes in pull requests

## License

This project is licensed under the GNU General Public License v3 (GPLv3) - see the [LICENSE](LICENSE) file for details.

## Summary of Changes

### 2026-08-15 - v0.5.1

Maintenance release. There are no changes to `acc-fwu`'s behaviour, CLI, or runtime dependency set — upgrading from v0.5.0 is optional.

- **Dependency & Build Updates**:
  - Upgraded pinned development requirements: `certifi` 2026.6.17 → 2026.7.22 and `charset-normalizer` 3.4.8 → 3.5.0. These pins are used for local development and CI; the published package still declares an unpinned `requests` dependency, so installed environments are unaffected.
  - Raised the build requirements to `setuptools>=83.0.0` and `setuptools_scm>=10.2.1`.
- **CI/CD**:
  - Removed Snyk from the `scan` job. Bandit remains in-pipeline, with CodeQL and dependency review running as separate workflows.
- **Development**:
  - Added a dev container (`.devcontainer/devcontainer.json`) pinning the Python 3.14 toolchain, with the virtualenv on a named volume and the project installed in editable mode on create.

### 2026-07-09 - v0.5.0

- **Breaking Changes**:
  - `python_requires` is now `>=3.14` (was `>=3.9`). Users on older Python versions must stay on v0.4.0 or upgrade their interpreter.
  - `acc-fwu` now exits **2** when any LKE cluster or managed database failed to update (previously it exited 0 and the failure was only visible in the printed summary). Scripts that treat any non-zero exit as fatal are unaffected; scripts that only checked for exit 1 should be reviewed.
- **New Features**:
  - Added `--lke-enable-acl`. By default an LKE/LKE-E cluster's `enabled` state is preserved, so an IP added to a *disabled* Control Plane ACL is stored but not enforced. This switch enables the ACL as the IP is added, so the rule takes effect immediately. Ignored with `-r/--remove`.
  - Added `--db-enable-firewall`. Managed databases have no firewall on/off toggle — the `allow_list` *is* the firewall, and an entry of `0.0.0.0/0` (or `::/0`) leaves it open to the internet. This switch strips those open ranges while adding your IP. The IP is always added before the ranges are removed, so the `allow_list` is never left empty. Ignored with `-r/--remove`.
- **Improvements**:
  - Failures now print to `stderr` unconditionally, even under `--quiet` — quiet mode silences informational output, not diagnostics — so failed cron runs leave a trail in logs or cron mail.
  - Expected skips (unsupported database engines, VPC-attached databases) are counted as `skipped` rather than `failed`, respect `--quiet`, and do not affect the exit code. Summaries gain a `skipped=` field.
- **Dependency & Build Updates**:
  - Upgraded `certifi` 2026.4.22 → 2026.6.17, `charset-normalizer` 3.4.7 → 3.4.8, `idna` 3.13 → 3.18, `requests` 2.33.1 → 2.34.2, and `urllib3` 2.6.3 → 2.7.0.
  - Raised the `setuptools_scm` build requirement to `>=10.2.0` and added the `Programming Language :: Python :: 3.14` classifier.
  - Bumped GitHub Actions to Node.js 24-compatible versions.
- **Tests**:
  - Total test count is now 198, up from 172, covering the two new switches, the exit-code contract, and the skipped-vs-failed distinction.

### 2026-05-10 - v0.4.0

- **New Features**:
  - Linode Managed Database (MySQL / PostgreSQL) `allow_list` updates now run by default alongside firewall and LKE updates — your public IP is added to (or removed from) every database's `allow_list` on each invocation. Pass `--no-database` to opt out, or use `--database` for a databases-only run. `--lke` and `--database` compose, e.g. `acc-fwu --lke --database` skips firewall and runs both.
  - Added `--database --list` to enumerate every Managed Database on the account (engine, ID, label, region, current `allow_list`).
  - VPC-attached databases (those with `private_network` set) are detected and skipped with a clear notice — the public IP we detect from ipify cannot reach a VPC-only endpoint, so updating their `allow_list` would be a no-op or worse, lock you out.
- **Improvements**:
  - Standardized output across every deployment type (firewall, LKE, database). All three now emit identically shaped lifecycle messages — target identifier (`<type> '<label>' (ID: <id>)`), preamble, result, no-op, dry-run, skip, and summary — via a shared `output.py` module. No more per-deployment-type phrasing drift.
  - Remove, dry-run, and no-op paths in the firewall flow now also flow through the shared formatters and honour `--quiet`, so automated scripts get no output when they ask for none.
  - Public IP detection is process-cached via `lru_cache`, so a single run hits `api.ipify.org` exactly once across the firewall, LKE, and database paths instead of three times.
- **Dependency & Build Updates**:
  - Upgraded `certifi` 2026.2.25 → 2026.4.22 and `idna` 3.11 → 3.13.
  - Relaxed `setuptools-scm` build requirement to `>=9.2.2` to keep up with upstream and unblock Python 3.14 build environments.
- **Tests**:
  - Total test count is now 172, up from 110. New modules: `tests/test_databases.py` (27 tests covering listing, allow_list mutation, orchestrator failure isolation, VPC skip) and `tests/test_output.py` (19 tests covering every shared formatter). Existing CLI and firewall test classes were extended for the new flags and shared output behaviour.

### 2026-04-18 - v0.3.1

- **New Features**:
  - LKE/LKE-E Control Plane ACL updates now run by default alongside firewall rule updates — no separate invocation needed. Pass `--no-lke` to opt out, or keep `--lke` for LKE-only runs.
  - `acc-fwu` now prints the saved firewall (ID + label) it's operating on whenever configuration is loaded from `~/.acc-fwu-config`, so you can see exactly which firewall is being touched.
  - `--list` tables (both firewalls and LKE clusters) now auto-size each column to its widest value, so long names like `resilio-sync-jumpbox-fw-e4e83e29` no longer break alignment.
- **Dependency & Build Updates**:
  - Upgraded `requests` 2.32.5 → 2.33.1 (addresses CVE-2026-25645, insecure temp file reuse in `extract_zipped_paths`).
  - Upgraded `certifi` to 2026.2.25 and `charset-normalizer` to 3.4.7.
  - Moved `setuptools_scm` to `pyproject.toml` `build-system.requires` so PEP 517 build isolation handles it, fixing the `vcs_versioning` import failure seen on Python 3.14 + setuptools 82.

### 2026-04-17 - v0.3.0

- **New Features**:
  - Added `--lke` flag to automate Linode Kubernetes Engine (LKE) and LKE-Enterprise (LKE-E) Control Plane ACL updates. Combined with the existing flags: `--lke` adds your public IP to every cluster's ACL, `--lke --remove` removes it, `--lke --list` enumerates clusters, and `--lke --dry-run` previews the change set.
- **Improvements**:
  - ACL updates preserve each cluster's existing `enabled` state and IPv6 entries, only mutating the IPv4 list.
  - Per-cluster failures (HTTP errors fetching or updating an ACL) are reported and counted without aborting the overall run.

### 2026-02-19 - v0.2.2

- **Bug Fixes**:
  - Fixed `list_firewalls()` only returning the first page of results - users with many firewalls would see incomplete lists in both `--list` output and interactive selection. All pages are now fetched.
- **Improvements**:
  - Extracted `LINODE_API_PAGE_SIZE` constant for the API page size value
  - Refactored code to reduce cognitive complexity: extracted helper functions in `cli.py` and `firewall.py`, added `CONTENT_TYPE_JSON` constant, simplified regex patterns

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
