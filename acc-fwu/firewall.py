import os
import requests
import configparser

REQUESTS_TIMEOUT = 5 # Request timeout in seconds
CONFIG_FILE_PATH = os.path.expanduser("~/.acc-fwu-config")
LINODE_CLI_CONFIG_PATH = os.path.expanduser("~/.config/linode-cli")

def load_config():
    """
    Load the saved `firewall_id` and `label` from the configuration file.

    Returns:
        tuple: A tuple containing the `firewall_id` and `label` if they exist,
            otherwise `(None, None)`.
    """
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE_PATH):
        config.read(CONFIG_FILE_PATH)
        # ConfigParser.get() returns None if the key does not exist
        firewall_id = config.get("DEFAULT", "firewall_id", fallback=None)
        label = config.get("DEFAULT", "label", fallback=None)
        return firewall_id, label
    return None, None

def save_config(firewall_id, label):
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "firewall_id": firewall_id,
        "label": label
    }
    with open(CONFIG_FILE_PATH, "w") as configfile:
        config.write(configfile)
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

def update_firewall_rule(firewall_id=None, label=None, debug=False):
    """
    Update the firewall rules for a given firewall ID and label.

    This function updates the firewall rules by adding or updating rules for TCP, UDP, and ICMP protocols.
    It first loads the firewall ID and label from the configuration file if they are not provided as arguments.
    Then it gets the API token and the public IP address of the machine running the script.
    It makes a request to get the existing firewall rules and checks if any of the new rules already exist.
    If a rule does not exist, it is added to the list of new rules.
    The existing rules and new rules are combined and replaced with the updated list of rules.

    Args:
        firewall_id (str): The ID of the firewall.
        label (str): The label for the firewall rule.
        debug (bool): If True, prints the existing rules data for debugging purposes.

    Raises:
        ValueError: If the firewall ID and label are not provided either as arguments or in the config file.
    """
    # Load the firewall ID and label from the configuration file if they are not provided as arguments
    if firewall_id is None or label is None:
        firewall_id, label = load_config()
        if firewall_id is None or label is None:
            raise ValueError("Firewall ID and rule label must be provided either as arguments or in the config file.")
    else:
        save_config(firewall_id, label)
    
    # Get the API token
    api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Get the public IP address of the machine running the script
    ip_address = get_public_ip() + "/32"  # Append /32 to the IP address

    # List of protocols to create rules for
    protocols = ["TCP", "UDP", "ICMP"]

    # Get existing rules
    response = requests.get(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules", headers=headers)
    response.raise_for_status()
    existing_rules = response.json()["inbound"]

    if debug:
        # Debugging output to inspect the structure of existing rules
        print("Existing rules data:", existing_rules)

    new_rules = []
    for protocol in protocols:
        # Create a new firewall rule for each protocol
        firewall_rule = {
            "label": f"{label}-{protocol}",  # Append protocol to the label
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

        # Check if a rule with the same label already exists
        rule_exists = any(rule for rule in existing_rules if rule["label"] == firewall_rule["label"])
        if not rule_exists:
            new_rules.append(firewall_rule)

    # Combine existing rules with new rules, avoiding duplicates
    combined_rules = existing_rules + new_rules

    # Replace all inbound rules with the updated list
    response = requests.put(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules",
                            headers=headers, json={"inbound": combined_rules})
    if response.status_code != 200:
        print("Response status code:", response.status_code)
        print("Response content:", response.content)
        response.raise_for_status()
    
    print(f"Created/updated firewall rules for {label}")
