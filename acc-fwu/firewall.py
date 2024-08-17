import os
import requests
import configparser

CONFIG_FILE_PATH = os.path.expanduser("~/.acc-fwu-config")
LINODE_CLI_CONFIG_PATH = os.path.expanduser("~/.config/linode-cli")

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE_PATH):
        config.read(CONFIG_FILE_PATH)
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
    try:
        with open(LINODE_CLI_CONFIG_PATH, "r") as f:
            config = json.load(f)
            return config.get("default", {}).get("token")
    except FileNotFoundError:
        raise FileNotFoundError("Linode CLI configuration not found. Please ensure that linode-cli is configured.")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in Linode CLI configuration file.")

def get_public_ip():
    response = requests.get("https://api.ipify.org?format=json")
    response.raise_for_status()
    return response.json()["ip"]

def update_firewall_rule(firewall_id=None, label=None):
    if firewall_id is None or label is None:
        firewall_id, label = load_config()
        if firewall_id is None or label is None:
            raise ValueError("Firewall ID and rule label must be provided either as arguments or in the config file.")
    else:
        save_config(firewall_id, label)
    
    api_token = get_api_token()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    ip_address = get_public_ip()

    firewall_rule = {
        "label": label,
        "action": "ACCEPT",
        "protocol": "ALL",
        "ports": "0-65535",
        "addresses": {
            "ipv4": [ip_address],
            "ipv6": []
        }
    }

    # Get existing rules
    response = requests.get(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules", headers=headers)
    response.raise_for_status()
    rules = response.json()["inbound"]

    # Check if the rule exists
    for rule in rules:
        if rule["label"] == label:
            # Update existing rule
            rule_id = rule["id"]
            response = requests.put(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules/{rule_id}",
                                    headers=headers, json=firewall_rule)
            response.raise_for_status()
            print(f"Updated firewall rule: {label}")
            return

    # If the rule doesn't exist, create a new one
    rules.append(firewall_rule)
    response = requests.put(f"https://api.linode.com/v4/networking/firewalls/{firewall_id}/rules",
                            headers=headers, json={"inbound": rules})
    response.raise_for_status()
    print(f"Created new firewall rule: {label}")