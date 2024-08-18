# acc-firewall_updater

A tool to automatically update the [Akamai Connected Cloud (ACC) / Linode](https://www.akamai.com/cloud) firewall rules to allow your IP

## Description

`acc-fwu` is a command-line tool to automatically update [Linode](https://www.linode.com)/ACC firewall rules with your current IP address. This is particularly useful for dynamically updating firewall rules to allow access from changing IP addresses, like when you visit the gym or you're sat in an airport.

## Installation

You can install the package via `pip`:

```bash
pip install acc-fwu
```

Alternatively, you can install it directly from the source:

```bash
git clone https://github.com/johnybradshaw/acc-firewall_updater.git
cd acc-firewall_updater
pip install -e .
```

## Usage

### First-time Setup

The first time you use `acc-fwu`, you’ll need to provide your Linode/ACC Firewall ID and *optionally* the label for the rule you want to create or update:

```bash
acc-fwu --firewall_id <FIREWALL_ID> --label <RULE_LABEL>
```

For example:

```bash
acc-fwu --firewall_id 123456 --label "Allow-My-Current-IP"
```

This command will do two things:

1. It will create or update the firewall rule with your current public IP address.
1. It will save the `firewall_id` and `label` to a configuration file `(~/.acc-fwu-config)` for future use.

### Subsequent Usage

After the initial setup, you can simply run `acc-fwu` without needing to provide the `firewall_id` and `label` again:

```bash
acc-fwu
```

This will:

1. Load the saved `firewall_id` and `label` from the configuration file.
1. Update the firewall rule with your current public IP address.

### Updating the Configuration

If you need to change the `firewall_id` or `label`, you can do so by running:

```bash
acc-fwu --firewall_id <NEW_FIREWALL_ID> --label <NEW_RULE_LABEL>
```

This will update the configuration file with the new values.

### Removing Firewall Rules

You can remove the firewall rule by running:

```bash
acc-fwu --remove
```

## Configuration File

The `acc-fwu` tool saves the `firewall_id` and `label` in a configuration file located at `~/.acc-fwu-config`. This file is automatically managed by the tool, so you generally won’t need to edit it manually.

## Summary of Changes

### 2024-08-17

- **First-time Setup**: Instructions on how to set the `firewall_id` and `label` the first time you use the tool.
- **Subsequent Usage**: Information about running the tool without additional arguments after the initial setup.
- **Updating the Configuration**: Guidance on how to change the stored `firewall_id` and `label` if needed.
- **Configuration File**: Brief explanation of the config file and its location.
