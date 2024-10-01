import os
import requests
import configparser

# Constants
REQUESTS_TIMEOUT = 5 # Request timeout in seconds
CONFIG_FILE_PATH = os.path.expanduser("~/.acc-fwu-config") # Configuration file path
LINODE_CLI_CONFIG_PATH = os.path.expanduser("~/.config/linode-cli") # Linode CLI configuration path

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

def save_config(firewall_id, label):
    """
    Save the firewall ID and label to the configuration file.

    This function saves the firewall ID and label to the configuration file at
    `CONFIG_FILE_PATH`.

    Args:
        firewall_id (str): The ID of the firewall rule.
        label (str): The label of the firewall rule.

    Returns:
        None
    """
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    
    # Add the firewall ID and label to the default section
    config["DEFAULT"] = { 
        "firewall_id": firewall_id,
        "label": label
    }
    
    # Open the configuration file in write mode
    with open(CONFIG_FILE_PATH, "w") as configfile:
        config.write(configfile)
    
    # Print a success message
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
    """
    response = requests.get(
        "https://api.ipify.org?format=json",
        timeout=REQUESTS_TIMEOUT
    )
    # Get the IP address from the response JSON
    return response.json()["ip"]

def remove_firewall_rule(firewall_id, label, debug=False):
    api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Get existing rules
    response = requests.get(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules", 
                                headers=headers, timeout=REQUESTS_TIMEOUT)
    response.raise_for_status()
    existing_rules = response.json()["inbound"]

    if debug:
        print("Existing rules data before removal:", existing_rules)  # Debugging output

    # Filter out the rules that match the given label for all protocols
    filtered_rules = [
        rule for rule in existing_rules
        if not any(rule["label"] == f"{label}-{protocol}" for protocol in ["TCP", "UDP", "ICMP"])
    ]

    if len(filtered_rules) == len(existing_rules):
        print(f"No rules found with label '{label}' to remove.")
    else:
        # Replace all inbound rules with the filtered list
        response = requests.put(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules",
                                    headers=headers, json={"inbound": filtered_rules}, timeout=REQUESTS_TIMEOUT)
        if response.status_code != 200:
            print("Response status code:", response.status_code)
            print("Response content:", response.content)
            response.raise_for_status()

        print(f"Removed firewall rules for {label}")

    if debug:
        print("Remaining rules data after removal:", filtered_rules)  # Debugging output

def update_firewall_rule(firewall_id: str, label: str, debug: bool = False) -> None:
    """
    Update the firewall rules for the given firewall ID and label by adding or updating rules with the current public IP address.

    This function modifies existing rules that match the given label or creates new rules if they don't exist.

    Args:
        firewall_id (str): The ID of the firewall to update
        label (str): The label for the firewall rules
        debug (bool): Whether to print debugging output

    Returns:
        None
    """

    api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    ip_address = get_public_ip() + "/32"  # Append /32 to the IP address

    protocols = ["TCP", "UDP", "ICMP"]  # List of protocols to create rules for

    # Get existing rules
    response = requests.get(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules", 
                            headers=headers, timeout=REQUESTS_TIMEOUT)
    response.raise_for_status()
    existing_rules = response.json()["inbound"]

    if debug:
        print("Existing rules data:", existing_rules)  # Debugging output to inspect the structure

    updated_rules = []
    for protocol in protocols:
        rule_label = f"{label}-{protocol}"  # Create a label specific to the protocol
        firewall_rule = {
            "label": rule_label,
            "action": "ACCEPT",
            "protocol": protocol,
            "addresses": {
                "ipv4": [ip_address],
            }
        }

        # Only include the ipv6 field if it's not empty
        ipv6_addresses = []
        if ipv6_addresses:
            firewall_rule["addresses"]["ipv6"] = ipv6_addresses

        # Check if a rule with the same label exists
        rule_updated = False
        for rule in existing_rules:
            if rule["label"] == rule_label:
                # Update the existing rule with the new IP address
                rule["addresses"]["ipv4"] = [ip_address]
                rule_updated = True
                break

        if not rule_updated:
            updated_rules.append(firewall_rule)

    # Combine existing rules with the updated or new rules
    combined_rules = existing_rules + updated_rules

    # Replace all inbound rules with the updated list
    response = requests.put(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules",
                            headers=headers, json={"inbound": combined_rules}, 
                            timeout=REQUESTS_TIMEOUT)
    if response.status_code != 200:
        print("Response status code:", response.status_code)
        print("Response content:", response.content)
        response.raise_for_status()
    
    print(f"Created/updated firewall rules for {label} - [{ip_address}]")