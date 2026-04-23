import requests

from .firewall import (
    CONTENT_TYPE_JSON,
    LINODE_API_PAGE_SIZE,
    REQUESTS_TIMEOUT,
    get_api_token,
    get_public_ip,
)
from .output import (
    format_batch_preamble,
    format_dry_run,
    format_noop,
    format_result,
    format_skip,
    format_summary,
    format_target,
)

LINODE_LKE_BASE_URL = "https://api.linode.com/v4/lke/clusters"


def _auth_headers():
    """Build authorization headers for Linode API requests."""
    return {
        "Authorization": f"Bearer {get_api_token()}",
        "Content-Type": CONTENT_TYPE_JSON,
    }


def list_lke_clusters():
    """
    List all LKE and LKE-Enterprise clusters from the Linode API.

    The ``/lke/clusters`` endpoint returns both standard LKE and LKE-Enterprise
    (LKE-E) clusters; the ``tier`` field distinguishes them ("standard" vs.
    "enterprise"). Handles pagination like ``list_firewalls``.

    Returns:
        list: Dicts with keys ``id``, ``label``, ``region``, ``k8s_version``,
        ``tier``, and ``status``.
    """
    headers = _auth_headers()
    clusters = []
    page = 1

    while True:
        response = requests.get(
            LINODE_LKE_BASE_URL,
            headers=headers,
            params={"page": page, "page_size": LINODE_API_PAGE_SIZE},
            timeout=REQUESTS_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        clusters.extend(data.get("data", []))

        if page >= data.get("pages", 1):
            break
        page += 1

    return [
        {
            "id": c["id"],
            "label": c.get("label", ""),
            "region": c.get("region", ""),
            "k8s_version": c.get("k8s_version", ""),
            "tier": c.get("tier", "standard"),
            "status": c.get("status", "unknown"),
        }
        for c in clusters
    ]


def get_lke_acl(cluster_id, headers=None):
    """
    Retrieve the Control Plane ACL configuration for an LKE cluster.

    Args:
        cluster_id (int|str): The LKE cluster ID.
        headers (dict, optional): Reuse existing auth headers to avoid
            re-reading the token for each cluster.

    Returns:
        dict: The ``acl`` object from the API response. When no ACL has been
        configured yet, returns a sensible default structure so callers can
        treat every cluster uniformly.
    """
    if headers is None:
        headers = _auth_headers()

    response = requests.get(
        f"{LINODE_LKE_BASE_URL}/{cluster_id}/control_plane_acl",
        headers=headers,
        timeout=REQUESTS_TIMEOUT,
    )
    response.raise_for_status()
    acl = response.json().get("acl") or {}
    addresses = acl.get("addresses") or {}
    return {
        "enabled": acl.get("enabled", False),
        "addresses": {
            "ipv4": list(addresses.get("ipv4") or []),
            "ipv6": list(addresses.get("ipv6") or []),
        },
    }


def put_lke_acl(cluster_id, acl, headers=None, debug=False):
    """
    PUT an updated ACL configuration to an LKE cluster.

    Args:
        cluster_id (int|str): The LKE cluster ID.
        acl (dict): The ACL body (``{"enabled": ..., "addresses": {...}}``).
        headers (dict, optional): Reuse existing auth headers.
        debug (bool): Print request/response details on failure.
    """
    if headers is None:
        headers = _auth_headers()

    response = requests.put(
        f"{LINODE_LKE_BASE_URL}/{cluster_id}/control_plane_acl",
        headers=headers,
        json={"acl": acl},
        timeout=REQUESTS_TIMEOUT,
    )
    if response.status_code != 200:
        if debug:
            print("Response status code:", response.status_code)
            print("Response content:", response.content)
        response.raise_for_status()


def _format_cluster_label(cluster):
    """Return a human-readable identifier for logging."""
    tier = cluster.get("tier", "standard")
    type_name = "LKE-E" if tier == "enterprise" else "LKE"
    return format_target(type_name, cluster.get("label", ""), cluster["id"])


def _apply_ip_to_acl(acl, ip_with_mask, remove):
    """
    Apply the IP change to an ACL dict in-place-safe manner.

    Returns:
        tuple: (new_acl, changed, already_in_state)
          - new_acl: updated acl dict (copy)
          - changed: True if the ACL would change
          - already_in_state: True if no change needed (IP already
            present for add, or absent for remove)
    """
    ipv4 = list(acl.get("addresses", {}).get("ipv4", []))
    ipv6 = list(acl.get("addresses", {}).get("ipv6", []))

    if remove:
        if ip_with_mask not in ipv4:
            return acl, False, True
        ipv4 = [ip for ip in ipv4 if ip != ip_with_mask]
    else:
        if ip_with_mask in ipv4:
            return acl, False, True
        ipv4.append(ip_with_mask)

    new_acl = {
        "enabled": acl.get("enabled", False),
        "addresses": {"ipv4": ipv4, "ipv6": ipv6},
    }
    return new_acl, True, False


def _fetch_acl_safe(cluster, cluster_label, quiet, headers):
    """Fetch ACL for a cluster, returning None on HTTP failure."""
    try:
        return get_lke_acl(cluster["id"], headers=headers)
    except requests.RequestException as e:
        if not quiet:
            print(format_skip(cluster_label, f"failed to fetch ACL ({e})"))
        return None


def _commit_acl_change(cluster, cluster_label, new_acl, headers, debug, quiet):
    """PUT the updated ACL, returning True on success."""
    try:
        put_lke_acl(cluster["id"], new_acl, headers=headers, debug=debug)
        return True
    except requests.RequestException as e:
        if not quiet:
            print(format_skip(cluster_label, f"failed to update ({e})"))
        return False


def _report_unchanged(cluster_label, ip_with_mask, remove, quiet):
    if quiet:
        return
    print(format_noop(ip_with_mask, cluster_label, remove=remove))


def _maybe_warn_disabled(acl, cluster_label, remove, quiet):
    if not acl.get("enabled") and not remove and not quiet:
        print(f"Warning: Control Plane ACL is disabled on {cluster_label}; "
              "address will be stored but not enforced until ACL is enabled.")


def _process_cluster(cluster, ip_with_mask, remove, debug, quiet, dry_run, headers):
    """Apply the IP change to a single cluster's Control Plane ACL."""
    cluster_label = _format_cluster_label(cluster)

    acl = _fetch_acl_safe(cluster, cluster_label, quiet, headers)
    if acl is None:
        return "failed"

    if debug:
        print(f"Current ACL for {cluster_label}: {acl}")

    new_acl, changed, _ = _apply_ip_to_acl(acl, ip_with_mask, remove)
    if not changed:
        _report_unchanged(cluster_label, ip_with_mask, remove, quiet)
        return "unchanged"

    if dry_run:
        if not quiet:
            print(format_dry_run(ip_with_mask, cluster_label, remove=remove))
        return "changed"

    _maybe_warn_disabled(acl, cluster_label, remove, quiet)

    if not _commit_acl_change(cluster, cluster_label, new_acl, headers, debug, quiet):
        return "failed"

    if not quiet:
        print(format_result(ip_with_mask, cluster_label, remove=remove))
    return "changed"


def update_all_lke_acls(debug=False, quiet=False, dry_run=False, remove=False, implicit=False):
    """
    Add (or remove) the current public IP on every LKE/LKE-E Control Plane ACL.

    Args:
        debug (bool): Print verbose ACL state and API error details.
        quiet (bool): Suppress informational output.
        dry_run (bool): Show the planned changes without calling the PUT API.
        remove (bool): Remove the IP instead of adding it.
        implicit (bool): True when this call is part of the default firewall+LKE
            run (i.e., user did not pass ``--lke`` explicitly). Suppresses the
            "No LKE clusters found" notice so users without LKE see no noise.

    Returns:
        dict: Summary counts: ``changed``, ``unchanged``, ``failed``, ``total``.
    """
    headers = _auth_headers()
    clusters = list_lke_clusters()

    if not clusters:
        if not quiet and not implicit:
            print("No LKE clusters found in your Linode account.")
        return {"changed": 0, "unchanged": 0, "failed": 0, "total": 0}

    ip_with_mask = f"{get_public_ip()}/32"

    if not quiet:
        print(format_batch_preamble(ip_with_mask, "LKE cluster(s)", len(clusters), remove=remove))

    counts = {"changed": 0, "unchanged": 0, "failed": 0, "total": len(clusters)}
    for cluster in clusters:
        result = _process_cluster(cluster, ip_with_mask, remove, debug, quiet, dry_run, headers)
        counts[result] = counts.get(result, 0) + 1

    if not quiet:
        print(format_summary(counts))

    return counts
