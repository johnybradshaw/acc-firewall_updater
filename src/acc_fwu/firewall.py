import os
import re
import stat
import requests
import configparser

# Constants
REQUESTS_TIMEOUT = 5  # Request timeout in seconds
CONFIG_FILE_PATH = os.path.expanduser("~/.acc-fwu-config")  # Configuration file path
LINODE_CLI_CONFIG_PATH = os.path.expanduser("~/.config/linode-cli")  # Linode CLI configuration path

# Validation patterns
FIREWALL_ID_PATTERN = re.compile(r"^\d+$")  # Numeric firewall IDs only
LABEL_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")  # Alphanumeric, underscore, hyphen, max 32 chars
IPV4_PATTERN = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")


def validate_firewall_id(firewall_id):
    """
    Validate that the firewall ID is a numeric string.

    Args:
        firewall_id (str): The firewall ID to validate.

    Returns:
        bool: True if valid.

    Raises:
        ValueError: If the firewall ID is invalid.
    """
    if not firewall_id or not FIREWALL_ID_PATTERN.match(str(firewall_id)):
        raise ValueError(f"Invalid firewall ID: must be numeric, got '{firewall_id}'")
    return True


def validate_label(label):
    """
    Validate that the label is safe for use in API requests.

    Args:
        label (str): The label to validate.

    Returns:
        bool: True if valid.

    Raises:
        ValueError: If the label is invalid.
    """
    if not label or not LABEL_PATTERN.match(label):
        raise ValueError(
            f"Invalid label: must be 1-32 alphanumeric characters, underscores, or hyphens, got '{label}'"
        )
    return True


def validate_ip_address(ip_address):
    """
    Validate that the IP address is a valid IPv4 address.

    Args:
        ip_address (str): The IP address to validate.

    Returns:
        bool: True if valid.

    Raises:
        ValueError: If the IP address is invalid.
    """
    if not ip_address or not IPV4_PATTERN.match(ip_address):
        raise ValueError(f"Invalid IPv4 address received: '{ip_address}'")
    return True

def load_config():
    """
    Load the firewall ID and label from the configuration file.

    This function reads the configuration file located at `CONFIG_FILE_PATH` and
    retrieves the firewall ID and label. If the configuration file does not exist,
    a `FileNotFoundError` is raised.

    Returns:
        tuple: A tuple containing the firewall ID and label.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
    """
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    # Check if the configuration file exists
    if os.path.exists(CONFIG_FILE_PATH):
        # Read the configuration file
        config.read(CONFIG_FILE_PATH)

        # Get the firewall ID and label from the configuration
        firewall_id = config.get("DEFAULT", "firewall_id", fallback=None)
        label = config.get("DEFAULT", "label", fallback=None)

        # Return the firewall ID and label
        return firewall_id, label
    else:
        # Raise an error if the configuration file does not exist
        raise FileNotFoundError(
            f"No configuration file found at {CONFIG_FILE_PATH}. "
            "Please run the script with --firewall_id and --label first."
        )

def save_config(firewall_id, label, quiet=False):
    """
    Save the firewall ID and label to the configuration file.

    This function saves the firewall ID and label to the configuration file at
    `CONFIG_FILE_PATH` with secure permissions (readable only by owner).

    Args:
        firewall_id (str): The ID of the firewall rule.
        label (str): The label of the firewall rule.
        quiet (bool): If True, suppress output messages.

    Returns:
        None

    Raises:
        ValueError: If firewall_id or label are invalid.
    """
    # Validate inputs before saving
    validate_firewall_id(firewall_id)
    validate_label(label)

    # Create a ConfigParser object
    config = configparser.ConfigParser()

    # Add the firewall ID and label to the default section
    config["DEFAULT"] = {
        "firewall_id": firewall_id,
        "label": label
    }

    # Open the configuration file in write mode with secure permissions
    # Create file with restrictive permissions (owner read/write only)
    old_umask = os.umask(0o077)
    try:
        with open(CONFIG_FILE_PATH, "w") as configfile:
            config.write(configfile)
        # Ensure permissions are set correctly even if file existed
        os.chmod(CONFIG_FILE_PATH, stat.S_IRUSR | stat.S_IWUSR)
    finally:
        os.umask(old_umask)

    # Print a success message
    if not quiet:
        print(f"Configuration saved to {CONFIG_FILE_PATH}")

def get_api_token():
    """
    Load the API token from the Linode CLI configuration.

    This function will raise a FileNotFoundError if the Linode CLI configuration
    is not found, and a ValueError if the configuration does not contain a
    default user or an API token.

    Returns:
        str: The API token.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(LINODE_CLI_CONFIG_PATH): 
        raise FileNotFoundError("Linode CLI configuration not found. Please ensure that linode-cli is configured.")
    config.read(LINODE_CLI_CONFIG_PATH)
    
    # Get the default user
    user_section = config["DEFAULT"].get("default-user")
    if not user_section:
        raise ValueError("No default user specified in Linode CLI configuration.")
    
    # Get the API token
    api_token = config[user_section].get("token")
    if not api_token:
        raise ValueError("No API token found in the Linode CLI configuration.")
    
    return api_token

def get_public_ip():
    """
    Get the public IP address of the machine running this script.

    This function makes an HTTP request to the 'api.ipify.org' service to
    get the public IP address of the machine.

    Returns:
        str: The public IP address of the machine.

    Raises:
        ValueError: If the returned IP address is invalid.
        requests.RequestException: If the HTTP request fails.
    """
    response = requests.get(
        "https://api.ipify.org?format=json",
        timeout=REQUESTS_TIMEOUT
    )
    response.raise_for_status()

    # Get the IP address from the response JSON
    ip_address = response.json().get("ip")

    # Validate the IP address before returning
    validate_ip_address(ip_address)

    return ip_address

def remove_firewall_rule(firewall_id, label, debug=False, quiet=False, dry_run=False):
    """
    Remove firewall rules matching the given label.

    Args:
        firewall_id (str): The ID of the firewall.
        label (str): The label prefix of rules to remove.
        debug (bool): If True, print debug information.
        quiet (bool): If True, suppress output messages.
        dry_run (bool): If True, show what would be removed without making changes.

    Raises:
        ValueError: If firewall_id or label are invalid.
    """
    # Validate inputs
    validate_firewall_id(firewall_id)
    validate_label(label)

    api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Get existing rules
    response = requests.get(
        f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules",
        headers=headers,
        timeout=REQUESTS_TIMEOUT
    )
    response.raise_for_status()
    existing_rules = response.json().get("inbound", [])

    if debug:
        print("Existing rules data before removal:", existing_rules)

    # Filter out the rules that match the given label for all protocols
    protocols = ["TCP", "UDP", "ICMP"]
    filtered_rules = [
        rule for rule in existing_rules
        if not any(rule.get("label") == f"{label}-{protocol}" for protocol in protocols)
    ]

    rules_to_remove = len(existing_rules) - len(filtered_rules)

    if rules_to_remove == 0:
        if not quiet:
            print(f"No rules found with label '{label}' to remove.")
        return

    if dry_run:
        print(f"[DRY RUN] Would remove {rules_to_remove} rule(s) with label '{label}'")
        return

    # Replace all inbound rules with the filtered list
    response = requests.put(
        f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules",
        headers=headers,
        json={"inbound": filtered_rules},
        timeout=REQUESTS_TIMEOUT
    )
    if response.status_code != 200:
        if debug:
            print("Response status code:", response.status_code)
            print("Response content:", response.content)
        response.raise_for_status()

    if not quiet:
        print(f"Removed {rules_to_remove} firewall rule(s) for {label}")

    if debug:
        print("Remaining rules data after removal:", filtered_rules)

def update_firewall_rule(
    firewall_id: str,
    label: str,
    debug: bool = False,
    quiet: bool = False,
    dry_run: bool = False
) -> None:
    """
    Update firewall rules by adding or updating rules with the current public IP address.

    This function modifies existing rules that match the given label or creates
    new rules if they don't exist.

    Args:
        firewall_id (str): The ID of the firewall to update.
        label (str): The label for the firewall rules.
        debug (bool): Whether to print debugging output.
        quiet (bool): If True, suppress output messages.
        dry_run (bool): If True, show what would be changed without making changes.

    Returns:
        None

    Raises:
        ValueError: If firewall_id or label are invalid.
    """
    # Validate inputs
    validate_firewall_id(firewall_id)
    validate_label(label)

    api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    ip_address = get_public_ip()
    ip_with_mask = f"{ip_address}/32"

    protocols = ["TCP", "UDP", "ICMP"]

    # Get existing rules
    response = requests.get(
        f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules",
        headers=headers,
        timeout=REQUESTS_TIMEOUT
    )
    response.raise_for_status()
    existing_rules = response.json().get("inbound", [])

    if debug:
        print("Existing rules data:", existing_rules)

    updated_rules = []
    rules_updated_count = 0
    rules_created_count = 0

    for protocol in protocols:
        rule_label = f"{label}-{protocol}"
        firewall_rule = {
            "label": rule_label,
            "action": "ACCEPT",
            "protocol": protocol,
            "addresses": {
                "ipv4": [ip_with_mask],
            }
        }

        # Check if a rule with the same label exists
        rule_updated = False
        for rule in existing_rules:
            if rule.get("label") == rule_label:
                # Update the existing rule with the new IP address
                rule["addresses"]["ipv4"] = [ip_with_mask]
                rule_updated = True
                rules_updated_count += 1
                break

        if not rule_updated:
            updated_rules.append(firewall_rule)
            rules_created_count += 1

    # Combine existing rules with the updated or new rules
    combined_rules = existing_rules + updated_rules

    if dry_run:
        print(f"[DRY RUN] Would update {rules_updated_count} and create {rules_created_count} "
              f"rule(s) for {label} with IP {ip_with_mask}")
        return

    # Replace all inbound rules with the updated list
    response = requests.put(
        f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules",
        headers=headers,
        json={"inbound": combined_rules},
        timeout=REQUESTS_TIMEOUT
    )
    if response.status_code != 200:
        if debug:
            print("Response status code:", response.status_code)
            print("Response content:", response.content)
        response.raise_for_status()

    if not quiet:
        print(f"Created/updated firewall rules for {label} - [{ip_with_mask}]")