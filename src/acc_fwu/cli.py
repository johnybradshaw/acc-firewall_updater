import argparse
import sys
from .firewall import (
    CONFIG_FILE_PATH,
    update_firewall_rule,
    remove_firewall_rule,
    load_config,
    save_config,
    validate_firewall_id,
    validate_label,
    list_firewalls,
    select_firewall,
)
from .lke import list_lke_clusters, update_all_lke_acls
from .databases import list_databases, update_all_database_acls
from .output import format_target

# Version is set dynamically by setuptools_scm, fallback for development
try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("acc-fwu")
    except PackageNotFoundError:
        __version__ = "0.0.0-dev"
except ImportError:
    __version__ = "0.0.0-dev"


def _print_table(title, headers, rows):
    """Print a table with columns auto-sized to their widest row."""
    widths = [
        max(len(h), *(len(str(row[i])) for row in rows))
        for i, h in enumerate(headers)
    ]
    total = sum(widths) + 2 * (len(headers) - 1)

    print(f"\n{title}")
    print("-" * total)
    print("  ".join(f"{h:<{w}}" for h, w in zip(headers, widths)))
    print("-" * total)
    for row in rows:
        print("  ".join(f"{str(v):<{w}}" for v, w in zip(row, widths)))
    print("-" * total)


def _handle_list_command(debug):
    """Handle the --list command to display available firewalls."""
    firewalls = list_firewalls()
    if not firewalls:
        print("No firewalls found in your Linode account.")
        return

    rows = [(fw["id"], fw["label"], fw["status"]) for fw in firewalls]
    _print_table("Available firewalls:", ["ID", "Label", "Status"], rows)


def _handle_lke_list_command():
    """Handle the --list command when combined with --lke."""
    clusters = list_lke_clusters()
    if not clusters:
        print("No LKE clusters found in your Linode account.")
        return

    rows = [
        (
            c["id"],
            c["label"],
            c["region"],
            "enterprise" if c.get("tier") == "enterprise" else "standard",
            c["status"],
        )
        for c in clusters
    ]
    _print_table(
        "Available LKE clusters:",
        ["ID", "Label", "Region", "Tier", "Status"],
        rows,
    )


def _handle_lke_command(args):
    """Handle LKE Control Plane ACL operations across all clusters."""
    if args.list:
        _handle_lke_list_command()
        return None
    return update_all_lke_acls(
        debug=args.debug,
        quiet=args.quiet,
        dry_run=args.dry_run,
        remove=args.remove,
        enable_acl=args.lke_enable_acl,
    )


def _handle_database_list_command():
    """Handle the --list command when combined with --database."""
    databases = list_databases()
    if not databases:
        print("No managed databases found in your Linode account.")
        return

    rows = [
        (
            db["id"],
            db["label"],
            db["region"],
            db.get("engine", ""),
            db.get("version", ""),
            db["status"],
        )
        for db in databases
    ]
    _print_table(
        "Available managed databases:",
        ["ID", "Label", "Region", "Engine", "Version", "Status"],
        rows,
    )


def _handle_database_command(args):
    """Handle managed database allow_list operations across all databases."""
    if args.list:
        _handle_database_list_command()
        return None
    return update_all_database_acls(
        debug=args.debug,
        quiet=args.quiet,
        dry_run=args.dry_run,
        remove=args.remove,
        enable_firewall=args.db_enable_firewall,
    )


def _resolve_config_from_file(args_label, quiet=False):
    """Load config from file, using args_label as fallback."""
    firewall_id, label = load_config()
    if label is None:
        label = args_label
    if not quiet:
        target = format_target("firewall", label, firewall_id)
        print(f"Using saved {target} (from {CONFIG_FILE_PATH})")
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
                        help="List available firewalls (or LKE clusters with --lke, "
                             "or managed databases with --database) and exit.")
    parser.add_argument("--lke", action="store_true",
                        help="Target LKE/LKE-E Control Plane ACLs; skip firewall rules. "
                             "Adds (or removes with -r) your current public IP to every "
                             "cluster's ACL. Combinable with --database.")
    parser.add_argument("--no-lke", action="store_true",
                        help="Skip the default LKE/LKE-E Control Plane ACL update. "
                             "By default, acc-fwu updates firewall rules, LKE ACLs, "
                             "and managed database allow_lists.")
    parser.add_argument("--lke-enable-acl", action="store_true",
                        help="When updating LKE/LKE-E clusters, also enable the Control "
                             "Plane ACL (firewall) if it is currently disabled, so the "
                             "added IP is actually enforced. No effect with -r/--remove.")
    parser.add_argument("--database", action="store_true",
                        help="Target managed database allow_lists; skip firewall rules. "
                             "Adds (or removes with -r) your current public IP to every "
                             "managed database's allow_list. Combinable with --lke.")
    parser.add_argument("--no-database", action="store_true",
                        help="Skip the default managed database allow_list update. "
                             "By default, acc-fwu updates firewall rules, LKE ACLs, "
                             "and managed database allow_lists.")
    parser.add_argument("--db-enable-firewall", action="store_true",
                        help="When updating managed databases, remove open ranges "
                             "(0.0.0.0/0, ::/0) from the allow_list so only "
                             "explicitly-allowed IPs can connect. No effect with -r/--remove.")
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
        return _resolve_config_from_file(args.label, quiet=args.quiet)
    except FileNotFoundError:
        return _resolve_config_interactive(args)


def _execute_firewall_operation(args, firewall_id, label):
    """Execute the firewall operation (update or remove)."""
    if args.remove:
        return remove_firewall_rule(firewall_id, label, debug=args.debug, quiet=args.quiet, dry_run=args.dry_run)
    return update_firewall_rule(firewall_id, label, debug=args.debug, quiet=args.quiet,
                                dry_run=args.dry_run, add_ip=args.add)


def _failed_count(counts):
    """Extract the failed count from an operation's summary counts."""
    if isinstance(counts, dict):
        return counts.get("failed", 0)
    return 0


def _run_implicit_batch_updates(args):
    """Run the LKE and managed database batch updates that follow a firewall change.

    Returns:
        int: Total number of failed targets across both batches.
    """
    common = {
        "debug": args.debug,
        "quiet": args.quiet,
        "dry_run": args.dry_run,
        "remove": args.remove,
        "implicit": True,
    }
    failed = 0
    if not args.no_lke:
        failed += _failed_count(update_all_lke_acls(enable_acl=args.lke_enable_acl, **common))
    if not args.no_database:
        failed += _failed_count(
            update_all_database_acls(enable_firewall=args.db_enable_firewall, **common)
        )
    return failed


def _dispatch(args):
    """Run the requested operations and return the number of failed targets."""
    if args.lke or args.database:
        # Explicit selectors: skip the firewall path and run whichever
        # resource types were requested. Combining --lke and --database is
        # supported and runs both in sequence.
        failed = 0
        if args.lke:
            failed += _failed_count(_handle_lke_command(args))
        if args.database:
            failed += _failed_count(_handle_database_command(args))
        return failed

    if args.list:
        _handle_list_command(args.debug)
        return 0

    firewall_id, label = _resolve_firewall_config(args)
    failed = _failed_count(_execute_firewall_operation(args, firewall_id, label))
    return failed + _run_implicit_batch_updates(args)


def main():
    """
    Main CLI entry point for acc-fwu.

    Parses command-line arguments and executes the appropriate firewall
    operation (update or remove rules).

    Exit codes: 0 on success, 1 on a fatal error, 2 when the run completed
    but one or more targets failed to update.
    """
    parser = _create_parser()
    args = parser.parse_args()

    try:
        if _dispatch(args):
            sys.exit(2)

    except (ValueError, EOFError, KeyboardInterrupt) as e:
        # Always print errors, even in quiet mode: --quiet silences
        # informational output, not diagnostics.
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.debug:
            raise
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
