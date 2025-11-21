import argparse
import sys
from .firewall import (
    update_firewall_rule,
    remove_firewall_rule,
    load_config,
    save_config,
    validate_firewall_id,
    validate_label,
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


def main():
    """
    Main CLI entry point for acc-fwu.

    Parses command-line arguments and executes the appropriate firewall
    operation (update or remove rules).
    """
    parser = argparse.ArgumentParser(
        description="Create, update, or remove Akamai Connected Cloud (Linode) "
                    "firewall rules with your current IP address.",
        epilog="Example: acc-fwu --firewall_id 12345 --label MyIP"
    )
    parser.add_argument(
        "--firewall_id",
        help="The numeric ID of the Linode firewall."
    )
    parser.add_argument(
        "--label",
        help="Label for the firewall rule (alphanumeric, underscores, hyphens, max 32 chars).",
        default="Default-Label"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug mode to show existing rules data."
    )
    parser.add_argument(
        "-r", "--remove",
        action="store_true",
        help="Remove the specified rules from the firewall."
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress output messages (useful for cron/scripting)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes."
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args()

    try:
        if args.firewall_id is None:
            try:
                firewall_id, label = load_config()
                if label is None:
                    label = args.label
            except FileNotFoundError as e:
                if not args.quiet:
                    print(
                        "No configuration file found. Please run the script with "
                        "--firewall_id (and optionally --label) to create the config file."
                    )
                sys.exit(1)
        else:
            # Validate inputs early
            try:
                validate_firewall_id(args.firewall_id)
                validate_label(args.label)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

            firewall_id, label = args.firewall_id, args.label
            if not args.dry_run:
                save_config(firewall_id, label, quiet=args.quiet)

        if args.remove:
            remove_firewall_rule(
                firewall_id,
                label,
                debug=args.debug,
                quiet=args.quiet,
                dry_run=args.dry_run
            )
        else:
            update_firewall_rule(
                firewall_id,
                label,
                debug=args.debug,
                quiet=args.quiet,
                dry_run=args.dry_run
            )

    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.debug:
            raise
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
