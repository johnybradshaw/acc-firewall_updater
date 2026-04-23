"""
Shared output formatting for acc-fwu deployment types.

Every deployment type (firewall, LKE, future databases) emits the same shape
of lifecycle messages, so they share a single set of formatters here. The
vocabulary is:

    target:    "<type> '<label>' (ID: <id>)" e.g. "firewall 'prod' (ID: 12)"
    preamble:  "Adding <ip> on <target>..."  (single)
               "Adding <ip> on N <type>(s)..."  (batch)
    result:    "Added <ip> on <target>"
    noop:      "<ip> already present on <target>, no changes needed"
    dry-run:   "[DRY RUN] Would add <ip> on <target>"
    skip:      "Skipping <target>: <reason>"
    summary:   "Done. changed=X unchanged=Y failed=Z total=W"
"""


def format_target(type_name, label, target_id):
    """Render a target identifier used in every output line.

    Args:
        type_name: Human label for the deployment type ("firewall", "LKE",
            "LKE-E", "database").
        label: The target's user-facing label.
        target_id: The target's numeric ID.
    """
    return f"{type_name} '{label}' (ID: {target_id})"


def _verb(remove, tense):
    """Return add/remove verbs in the requested tense.

    tense is one of: "present" (Adding/Removing), "past" (Added/Removed),
    "infinitive" (add/remove).
    """
    forms = {
        "present": ("Removing", "Adding"),
        "past": ("Removed", "Added"),
        "infinitive": ("remove", "add"),
    }
    remove_form, add_form = forms[tense]
    return remove_form if remove else add_form


def format_preamble(ip, target, remove=False):
    """Announce what the tool is about to do to a single target."""
    return f"{_verb(remove, 'present')} {ip} on {target}..."


def format_batch_preamble(ip, type_plural, count, remove=False):
    """Announce what the tool is about to do across a batch of targets."""
    return f"{_verb(remove, 'present')} {ip} on {count} {type_plural}..."


def format_result(ip, target, remove=False):
    """Render a successful per-target result line."""
    return f"{_verb(remove, 'past')} {ip} on {target}"


def format_noop(ip, target, remove=False):
    """Render a no-op line when the IP is already in the desired state."""
    state = "absent" if remove else "present"
    return f"{ip} already {state} on {target}, no changes needed"


def format_dry_run(ip, target, remove=False):
    """Render a dry-run line describing the planned change."""
    return f"[DRY RUN] Would {_verb(remove, 'infinitive')} {ip} on {target}"


def format_dry_run_noop(ip, target, remove=False):
    """Render a dry-run line when no change would be made."""
    return f"[DRY RUN] {format_noop(ip, target, remove=remove)}"


def format_skip(target, reason):
    """Render a skip line when a target cannot be processed."""
    return f"Skipping {target}: {reason}"


def format_summary(counts):
    """Render the end-of-stage counter summary."""
    return (
        f"Done. changed={counts.get('changed', 0)} "
        f"unchanged={counts.get('unchanged', 0)} "
        f"failed={counts.get('failed', 0)} "
        f"total={counts.get('total', 0)}"
    )
