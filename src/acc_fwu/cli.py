import argparse
import sys
from .firewall import (
    update_firewall_rule,
    remove_firewall_rule,
    load_config,
    save_config,
    validate_firewall_id,
    validate_label,
    list_firewalls,
    select_firewall,
)

# Version is set dynamically by setuptools_scm, fallback for development
try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("acc-fwu")
    except PackageNotFoundError:
        __version__ = "0.0.0-dev"
except ImportError:
    __version__ = "0.0.0-dev"


def _handle_list_command(debug):
    """Handle the --list command to display available firewalls."""
    firewalls = list_firewalls()
    if not firewalls:
        print("No firewalls found in your Linode account.")
        return

    print("\nAvailable firewalls:")
    print("-" * 60)
    print(f"{'ID':<12} {'Label':<30} {'Status':<15}")
    print("-" * 60)
    for fw in firewalls:
        print(f"{fw['id']:<12} {fw['label']:<30} {fw['status']:<15}")
    print("-" * 60)


def _resolve_config_from_file(args_label):
    """Load config from file, using args_label as fallback."""
    firewall_id, label = load_config()
    if label is None:
        label = args_label
    return firewall_id, label


def _resolve_config_interactive(args):
    """Handle interactive firewall selection when no config exists."""
    if not args.quiet:
        print("No configuration file found. Let's select a firewall.")

    firewall_id = select_firewall(quiet=args.quiet)
    label = args.label

    if not args.dry_run:
        save_config(firewall_id, label, quiet=args.quiet)

    return firewall_id, label


def _resolve_config_from_args(args):
    """Validate and use config from command-line arguments."""
    validate_firewall_id(args.firewall_id)
    validate_label(args.label)

    if not args.dry_run:
        save_config(args.firewall_id, args.label, quiet=args.quiet)

    return args.firewall_id, args.label


def _create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Create, update, or remove Akamai Connected Cloud (Linode) "
                    "firewall rules with your current IP address.",
        epilog="Example: acc-fwu --firewall_id 12345 --label MyIP"
    )
    parser.add_argument("--firewall_id", help="The numeric ID of the Linode firewall.")
    parser.add_argument(
        "--label",
        help="Label for the firewall rule (alphanumeric, underscores, hyphens, max 32 chars).",
        default="Default-Label"
    )
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Enable debug mode to show existing rules data.")
    parser.add_argument("-r", "--remove", action="store_true",
                        help="Remove the specified rules from the firewall.")
    parser.add_argument("-a", "--add", action="store_true",
                        help="Add IP to existing rules instead of replacing (useful for multiple locations).")
    parser.add_argument("-l", "--list", action="store_true",
                        help="List available firewalls and exit.")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress output messages (useful for cron/scripting).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making any changes.")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _resolve_firewall_config(args):
    """Resolve firewall configuration from args, config file, or interactive selection."""
    if args.firewall_id is not None:
        return _resolve_config_from_args(args)

    try:
        return _resolve_config_from_file(args.label)
    except FileNotFoundError:
        return _resolve_config_interactive(args)


def _execute_firewall_operation(args, firewall_id, label):
    """Execute the firewall operation (update or remove)."""
    if args.remove:
        remove_firewall_rule(firewall_id, label, debug=args.debug, quiet=args.quiet, dry_run=args.dry_run)
    else:
        update_firewall_rule(firewall_id, label, debug=args.debug, quiet=args.quiet,
                             dry_run=args.dry_run, add_ip=args.add)


def main():
    """
    Main CLI entry point for acc-fwu.

    Parses command-line arguments and executes the appropriate firewall
    operation (update or remove rules).
    """
    parser = _create_parser()
    args = parser.parse_args()

    try:
        if args.list:
            _handle_list_command(args.debug)
            return

        firewall_id, label = _resolve_firewall_config(args)
        _execute_firewall_operation(args, firewall_id, label)

    except (ValueError, EOFError, KeyboardInterrupt) as e:
        if not args.quiet:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.debug:
            raise
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
