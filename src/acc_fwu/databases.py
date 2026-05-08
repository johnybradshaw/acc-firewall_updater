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

LINODE_DATABASES_BASE_URL = "https://api.linode.com/v4/databases"
LINODE_DATABASES_LIST_URL = f"{LINODE_DATABASES_BASE_URL}/instances"

# Engines whose allow_list this tool knows how to update. The PUT endpoint is
# rooted at /databases/<engine>/instances/<id>, so any engine the API exposes
# in the listing but not here will be reported as a skip.
SUPPORTED_DB_ENGINES = ("mysql", "postgresql")


def _auth_headers():
    """Build authorization headers for Linode API requests."""
    return {
        "Authorization": f"Bearer {get_api_token()}",
        "Content-Type": CONTENT_TYPE_JSON,
    }


def list_databases():
    """
    List all managed database instances from the Linode API.

    The ``/databases/instances`` endpoint returns every Managed Database on the
    account regardless of engine. The instance object already contains the
    ``allow_list`` so callers do not need a second GET per database.

    Returns:
        list: Dicts with keys ``id``, ``label``, ``region``, ``engine``,
        ``version``, ``status``, ``platform``, and ``allow_list``.
    """
    headers = _auth_headers()
    databases = []
    page = 1

    while True:
        response = requests.get(
            LINODE_DATABASES_LIST_URL,
            headers=headers,
            params={"page": page, "page_size": LINODE_API_PAGE_SIZE},
            timeout=REQUESTS_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        databases.extend(data.get("data", []))

        if page >= data.get("pages", 1):
            break
        page += 1

    return [
        {
            "id": db["id"],
            "label": db.get("label", ""),
            "region": db.get("region", ""),
            "engine": db.get("engine", ""),
            "version": db.get("version", ""),
            "status": db.get("status", "unknown"),
            "platform": db.get("platform", ""),
            "allow_list": list(db.get("allow_list") or []),
        }
        for db in databases
    ]


def put_database_allow_list(database_id, engine, allow_list, headers=None, debug=False):
    """
    PUT an updated allow_list to a managed database instance.

    Args:
        database_id (int|str): The database instance ID.
        engine (str): The database engine, used in the URL path
            (``mysql`` or ``postgresql``).
        allow_list (list): The replacement list of CIDR/IP strings.
        headers (dict, optional): Reuse existing auth headers.
        debug (bool): Print request/response details on failure.
    """
    if headers is None:
        headers = _auth_headers()

    response = requests.put(
        f"{LINODE_DATABASES_BASE_URL}/{engine}/instances/{database_id}",
        headers=headers,
        json={"allow_list": allow_list},
        timeout=REQUESTS_TIMEOUT,
    )
    if response.status_code != 200:
        if debug:
            print("Response status code:", response.status_code)
            print("Response content:", response.content)
        response.raise_for_status()


def _format_database_label(database):
    """Return a human-readable identifier for logging."""
    engine = database.get("engine", "") or "database"
    type_name = f"{engine} database" if engine else "database"
    return format_target(type_name, database.get("label", ""), database["id"])


def _apply_ip_to_allow_list(allow_list, ip_with_mask, remove):
    """
    Apply the IP change to an allow_list in a copy-safe manner.

    Returns:
        tuple: (new_allow_list, changed, already_in_state)
          - new_allow_list: updated list (copy)
          - changed: True if the list would change
          - already_in_state: True if no change needed (IP already
            present for add, or absent for remove)
    """
    new_list = list(allow_list or [])

    if remove:
        if ip_with_mask not in new_list:
            return new_list, False, True
        new_list = [ip for ip in new_list if ip != ip_with_mask]
    else:
        if ip_with_mask in new_list:
            return new_list, False, True
        new_list.append(ip_with_mask)

    return new_list, True, False


def _commit_allow_list_change(database, db_label, new_list, headers, debug, quiet):
    """PUT the updated allow_list, returning True on success."""
    try:
        put_database_allow_list(
            database["id"],
            database["engine"],
            new_list,
            headers=headers,
            debug=debug,
        )
        return True
    except requests.RequestException as e:
        if not quiet:
            print(format_skip(db_label, f"failed to update ({e})"))
        return False


def _report_unchanged(db_label, ip_with_mask, remove, quiet):
    if quiet:
        return
    print(format_noop(ip_with_mask, db_label, remove=remove))


def _process_database(database, ip_with_mask, remove, debug, quiet, dry_run, headers):
    """Apply the IP change to a single database's allow_list."""
    db_label = _format_database_label(database)

    engine = database.get("engine", "")
    if engine not in SUPPORTED_DB_ENGINES:
        if not quiet:
            print(format_skip(db_label, f"unsupported engine '{engine}'"))
        return "failed"

    allow_list = database.get("allow_list", [])
    if debug:
        print(f"Current allow_list for {db_label}: {allow_list}")

    new_list, changed, _ = _apply_ip_to_allow_list(allow_list, ip_with_mask, remove)
    if not changed:
        _report_unchanged(db_label, ip_with_mask, remove, quiet)
        return "unchanged"

    if dry_run:
        if not quiet:
            print(format_dry_run(ip_with_mask, db_label, remove=remove))
        return "changed"

    if not _commit_allow_list_change(database, db_label, new_list, headers, debug, quiet):
        return "failed"

    if not quiet:
        print(format_result(ip_with_mask, db_label, remove=remove))
    return "changed"


def update_all_database_acls(debug=False, quiet=False, dry_run=False, remove=False, implicit=False):
    """
    Add (or remove) the current public IP on every managed database's allow_list.

    Args:
        debug (bool): Print verbose state and API error details.
        quiet (bool): Suppress informational output.
        dry_run (bool): Show the planned changes without calling the PUT API.
        remove (bool): Remove the IP instead of adding it.
        implicit (bool): True when this call is part of the default firewall+LKE
            +database run (i.e., user did not pass ``--database`` explicitly).
            Suppresses the "No managed databases found" notice so users without
            any databases see no extra output.

    Returns:
        dict: Summary counts: ``changed``, ``unchanged``, ``failed``, ``total``.
    """
    headers = _auth_headers()
    databases = list_databases()

    if not databases:
        if not quiet and not implicit:
            print("No managed databases found in your Linode account.")
        return {"changed": 0, "unchanged": 0, "failed": 0, "total": 0}

    ip_with_mask = f"{get_public_ip()}/32"

    if not quiet:
        print(format_batch_preamble(ip_with_mask, "managed database(s)", len(databases), remove=remove))

    counts = {"changed": 0, "unchanged": 0, "failed": 0, "total": len(databases)}
    for database in databases:
        result = _process_database(database, ip_with_mask, remove, debug, quiet, dry_run, headers)
        counts[result] = counts.get(result, 0) + 1

    if not quiet:
        print(format_summary(counts))

    return counts
