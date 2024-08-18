import argparse
from firewall import update_firewall_rule  # Import from the same directory since cli.py and firewall.py are in acc-fwu

def main():
    """
    Main entry point for the command-line tool.
    """
    parser = argparse.ArgumentParser(description="Create or update a Linode firewall rule with your current IP address.")
    parser.add_argument("--firewall_id", help="The ID of the Linode firewall to update.", required=False)
    parser.add_argument("--label", help="Label for the firewall rule to create or update.", required=False)
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode to show existing rules data.")
    args = parser.parse_args()

    # Run the firewall update function
    update_firewall_rule(args.firewall_id, args.label, debug=args.debug)
