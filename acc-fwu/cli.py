import argparse
from linode_firewall_tool.firewall import update_firewall_rule

def main():
    parser = argparse.ArgumentParser(description="Create or update a Linode firewall rule with your current IP address.")
    parser.add_argument("--firewall_id", help="The ID of the Linode firewall.", required=False)
    parser.add_argument("--label", help="Label for the firewall rule.", required=False)
    args = parser.parse_args()

    update_firewall_rule(args.firewall_id, args.label)