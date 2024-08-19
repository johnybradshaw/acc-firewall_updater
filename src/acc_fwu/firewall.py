import os
import requests
import configparser

REQUESTS_TIMEOUT = 5 # Request timeout in seconds
CONFIG_FILE_PATH = os.path.expanduser("~/.acc-fwu-config")
LINODE_CLI_CONFIG_PATH = os.path.expanduser("~/.config/linode-cli")

def load_config():
    config_path = os.path.expanduser("~/.acc-fwu-config")
    config = configparser.ConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)
        firewall_id = config.get("DEFAULT", "firewall_id", fallback=None)
        label = config.get("DEFAULT", "label", fallback=None)
        return firewall_id, label
    else:
        raise FileNotFoundError(f"No configuration file found at {config_path}. Please run the script with --firewall_id and --label first.")


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

def remove_firewall_rule(firewall_id, label, debug=False):
    api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Get existing rules
    response = requests.get(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules", headers=headers)
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
                                headers=headers, json={"inbound": filtered_rules})
        if response.status_code != 200:
            print("Response status code:", response.status_code)
            print("Response content:", response.content)
            response.raise_for_status()

        print(f"Removed firewall rules for {label}")

    if debug:
        print("Remaining rules data after removal:", filtered_rules)  # Debugging output

def update_firewall_rule(firewall_id, label, debug=False):
    api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    ip_address = get_public_ip() + "/32"  # Append /32 to the IP address

    protocols = ["TCP", "UDP", "ICMP"]  # List of protocols to create rules for

    # Get existing rules
    response = requests.get(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules", headers=headers)
    response.raise_for_status()
    existing_rules = response.json()["inbound"]

    if debug:
        print("Existing rules data:", existing_rules)  # Debugging output to inspect the structure

    new_rules = []
    for protocol in protocols:
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