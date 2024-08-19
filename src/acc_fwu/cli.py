import argparse
from .firewall import update_firewall_rule, remove_firewall_rule, load_config, save_config

def main():
    parser = argparse.ArgumentParser(description="Create, update, or remove Linode firewall rules with your current IP address.")
    parser.add_argument("--firewall_id", help="The ID of the Linode firewall.")
    parser.add_argument("--label", help="Label for the firewall rule.", default="Default-Label")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode to show existing rules data.")
    parser.add_argument("-r", "--remove", action="store_true", help="Remove the specified rules from the firewall.")
    args = parser.parse_args()

    if args.firewall_id is None:
        try:
            firewall_id, label = load_config()
            if label is None:
                label = args.label  # Use default or provided label if not in config
        except FileNotFoundError:
            print("No configuration file found. Please run the script with --firewall_id (and optionally --label) to create the config file.")
            return
    else:
        firewall_id, label = args.firewall_id, args.label
        save_config(firewall_id, label)  # Save the configuration

    if args.remove:
        remove_firewall_rule(firewall_id, label, debug=args.debug)
    else:
        update_firewall_rule(firewall_id, label, debug=args.debug)