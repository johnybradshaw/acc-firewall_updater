"""Tests for the shared output formatting module.

These tests lock in the exact strings so every deployment type (firewall,
LKE, and any future type like databases) shares the same lifecycle output.
"""
from acc_fwu.output import (
    format_batch_preamble,
    format_dry_run,
    format_dry_run_noop,
    format_noop,
    format_preamble,
    format_result,
    format_skip,
    format_summary,
    format_target,
)


class TestFormatTarget:
    def test_firewall(self):
        assert format_target("firewall", "prod", 12345) == "firewall 'prod' (ID: 12345)"

    def test_lke(self):
        assert format_target("LKE", "my-k8s", 67890) == "LKE 'my-k8s' (ID: 67890)"

    def test_lke_enterprise(self):
        assert format_target("LKE-E", "ent", 1) == "LKE-E 'ent' (ID: 1)"


class TestPreamble:
    def test_add(self):
        target = format_target("firewall", "prod", 1)
        assert format_preamble("1.2.3.4/32", target) == (
            "Adding 1.2.3.4/32 on firewall 'prod' (ID: 1)..."
        )

    def test_remove(self):
        target = format_target("LKE", "k", 2)
        assert format_preamble("1.2.3.4/32", target, remove=True) == (
            "Removing 1.2.3.4/32 on LKE 'k' (ID: 2)..."
        )

    def test_batch_add(self):
        assert format_batch_preamble("1.2.3.4/32", "LKE cluster(s)", 3) == (
            "Adding 1.2.3.4/32 on 3 LKE cluster(s)..."
        )

    def test_batch_remove(self):
        assert format_batch_preamble("1.2.3.4/32", "LKE cluster(s)", 3, remove=True) == (
            "Removing 1.2.3.4/32 on 3 LKE cluster(s)..."
        )


class TestResultAndNoop:
    def test_result_add(self):
        t = format_target("firewall", "x", 1)
        assert format_result("1.2.3.4/32", t) == "Added 1.2.3.4/32 on firewall 'x' (ID: 1)"

    def test_result_remove(self):
        t = format_target("LKE", "x", 1)
        assert format_result("1.2.3.4/32", t, remove=True) == (
            "Removed 1.2.3.4/32 on LKE 'x' (ID: 1)"
        )

    def test_noop_present(self):
        t = format_target("firewall", "x", 1)
        assert format_noop("1.2.3.4/32", t) == (
            "1.2.3.4/32 already present on firewall 'x' (ID: 1), no changes needed"
        )

    def test_noop_absent(self):
        t = format_target("LKE", "x", 1)
        assert format_noop("1.2.3.4/32", t, remove=True) == (
            "1.2.3.4/32 already absent on LKE 'x' (ID: 1), no changes needed"
        )


class TestDryRun:
    def test_dry_run_add(self):
        t = format_target("firewall", "x", 1)
        assert format_dry_run("1.2.3.4/32", t) == (
            "[DRY RUN] Would add 1.2.3.4/32 on firewall 'x' (ID: 1)"
        )

    def test_dry_run_remove(self):
        t = format_target("LKE", "x", 1)
        assert format_dry_run("1.2.3.4/32", t, remove=True) == (
            "[DRY RUN] Would remove 1.2.3.4/32 on LKE 'x' (ID: 1)"
        )

    def test_dry_run_noop(self):
        t = format_target("firewall", "x", 1)
        assert format_dry_run_noop("1.2.3.4/32", t) == (
            "[DRY RUN] 1.2.3.4/32 already present on firewall 'x' (ID: 1), no changes needed"
        )


class TestSkip:
    def test_skip_with_reason(self):
        t = format_target("LKE", "broken", 99)
        assert format_skip(t, "timed out") == "Skipping LKE 'broken' (ID: 99): timed out"


class TestSummary:
    def test_all_counts(self):
        assert format_summary(
            {"changed": 2, "unchanged": 1, "failed": 0, "total": 3}
        ) == "Done. changed=2 unchanged=1 failed=0 total=3"

    def test_missing_counts_default_zero(self):
        assert format_summary({"total": 1}) == (
            "Done. changed=0 unchanged=0 failed=0 total=1"
        )


class TestCrossDeploymentConsistency:
    """Ensure firewall + LKE + any future type produce identically shaped lines."""

    def test_firewall_and_lke_share_shape(self):
        fw = format_target("firewall", "prod", 1)
        lke = format_target("LKE", "prod", 1)
        # Both targets produce the same `result` shape, only the type word differs.
        fw_line = format_result("1.2.3.4/32", fw)
        lke_line = format_result("1.2.3.4/32", lke)
        assert fw_line.replace("firewall", "<TYPE>") == lke_line.replace("LKE", "<TYPE>")

    def test_future_database_type_fits_pattern(self):
        """A future 'database' deployment type must plug into the same helpers."""
        db = format_target("database", "users-db", 42)
        assert format_result("1.2.3.4/32", db) == (
            "Added 1.2.3.4/32 on database 'users-db' (ID: 42)"
        )
        assert format_noop("1.2.3.4/32", db) == (
            "1.2.3.4/32 already present on database 'users-db' (ID: 42), no changes needed"
        )
        assert format_dry_run("1.2.3.4/32", db, remove=True) == (
            "[DRY RUN] Would remove 1.2.3.4/32 on database 'users-db' (ID: 42)"
        )
