import pytest
import requests
from unittest import mock

from acc_fwu.databases import (
    LINODE_DATABASES_BASE_URL,
    LINODE_DATABASES_LIST_URL,
    _apply_ip_to_allow_list,
    list_databases,
    put_database_allow_list,
    update_all_database_acls,
)
from acc_fwu.firewall import LINODE_API_PAGE_SIZE


HEADERS = {"Authorization": "Bearer test-token", "Content-Type": "application/json"}


def _mock_response(json_data=None, status_code=200, raise_exc=None):
    resp = mock.Mock()
    resp.json.return_value = json_data if json_data is not None else {}
    resp.status_code = status_code
    resp.content = b""
    if raise_exc is not None:
        resp.raise_for_status = mock.Mock(side_effect=raise_exc)
    else:
        resp.raise_for_status = mock.Mock()
    return resp


class TestListDatabases:
    def test_returns_databases_with_engine_and_allow_list(self, monkeypatch):
        resp = _mock_response({
            "data": [
                {"id": 1, "label": "primary", "region": "us-east",
                 "engine": "mysql", "version": "8.0.30", "status": "active",
                 "platform": "rdbms-default",
                 "allow_list": ["1.2.3.4/32"]},
                {"id": 2, "label": "analytics", "region": "eu-west",
                 "engine": "postgresql", "version": "15", "status": "active",
                 "allow_list": []},
            ],
            "pages": 1,
        })
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=resp))
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))

        databases = list_databases()
        assert len(databases) == 2
        assert databases[0]["engine"] == "mysql"
        assert databases[0]["allow_list"] == ["1.2.3.4/32"]
        assert databases[1]["engine"] == "postgresql"
        assert databases[1]["allow_list"] == []

    def test_pagination(self, monkeypatch):
        page1 = _mock_response({
            "data": [{"id": 1, "label": "a", "region": "us", "engine": "mysql"}],
            "pages": 2,
        })
        page2 = _mock_response({
            "data": [{"id": 2, "label": "b", "region": "us", "engine": "postgresql"}],
            "pages": 2,
        })
        mock_get = mock.Mock(side_effect=[page1, page2])
        monkeypatch.setattr(requests, "get", mock_get)
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))

        databases = list_databases()
        assert [d["id"] for d in databases] == [1, 2]
        assert mock_get.call_args_list[0][1]["params"] == {"page": 1, "page_size": LINODE_API_PAGE_SIZE}
        assert mock_get.call_args_list[1][1]["params"] == {"page": 2, "page_size": LINODE_API_PAGE_SIZE}

    def test_uses_correct_url(self, monkeypatch):
        resp = _mock_response({"data": [], "pages": 1})
        mock_get = mock.Mock(return_value=resp)
        monkeypatch.setattr(requests, "get", mock_get)
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))

        list_databases()
        assert mock_get.call_args[0][0] == LINODE_DATABASES_LIST_URL

    def test_handles_missing_allow_list(self, monkeypatch):
        resp = _mock_response({"data": [{"id": 1, "engine": "mysql"}], "pages": 1})
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=resp))
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))

        databases = list_databases()
        assert databases[0]["allow_list"] == []
        assert databases[0]["label"] == ""


class TestPutDatabaseAllowList:
    def test_sends_allow_list_to_engine_specific_url(self, monkeypatch):
        resp = _mock_response(status_code=200)
        mock_put = mock.Mock(return_value=resp)
        monkeypatch.setattr(requests, "put", mock_put)

        put_database_allow_list(42, "mysql", ["9.9.9.9/32"], headers=HEADERS)

        assert mock_put.call_count == 1
        assert mock_put.call_args[0][0] == f"{LINODE_DATABASES_BASE_URL}/mysql/instances/42"
        assert mock_put.call_args[1]["json"] == {"allow_list": ["9.9.9.9/32"]}

    def test_postgresql_engine_in_url(self, monkeypatch):
        resp = _mock_response(status_code=200)
        mock_put = mock.Mock(return_value=resp)
        monkeypatch.setattr(requests, "put", mock_put)

        put_database_allow_list(7, "postgresql", [], headers=HEADERS)

        assert mock_put.call_args[0][0] == f"{LINODE_DATABASES_BASE_URL}/postgresql/instances/7"

    def test_raises_on_error_status(self, monkeypatch):
        resp = _mock_response(
            status_code=400,
            raise_exc=requests.exceptions.HTTPError("400"),
        )
        resp.content = b'{"errors": [{"reason": "bad"}]}'
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=resp))

        with pytest.raises(requests.exceptions.HTTPError):
            put_database_allow_list(42, "mysql", [], headers=HEADERS, debug=True)


class TestApplyIpToAllowList:
    def test_add_when_absent_adds(self):
        new_list, changed, already = _apply_ip_to_allow_list(
            ["1.1.1.1/32"], "2.2.2.2/32", remove=False,
        )
        assert changed is True
        assert already is False
        assert "2.2.2.2/32" in new_list
        assert "1.1.1.1/32" in new_list

    def test_add_when_present_noop(self):
        _, changed, already = _apply_ip_to_allow_list(
            ["2.2.2.2/32"], "2.2.2.2/32", remove=False,
        )
        assert changed is False
        assert already is True

    def test_remove_when_present_removes(self):
        new_list, changed, already = _apply_ip_to_allow_list(
            ["2.2.2.2/32", "1.1.1.1/32"], "2.2.2.2/32", remove=True,
        )
        assert changed is True
        assert already is False
        assert "2.2.2.2/32" not in new_list
        assert new_list == ["1.1.1.1/32"]

    def test_remove_when_absent_noop(self):
        _, changed, already = _apply_ip_to_allow_list(
            ["1.1.1.1/32"], "2.2.2.2/32", remove=True,
        )
        assert changed is False
        assert already is True

    def test_handles_none_allow_list(self):
        new_list, changed, _ = _apply_ip_to_allow_list(None, "2.2.2.2/32", remove=False)
        assert changed is True
        assert new_list == ["2.2.2.2/32"]

    def test_does_not_mutate_input(self):
        original = ["1.1.1.1/32"]
        new_list, _, _ = _apply_ip_to_allow_list(original, "2.2.2.2/32", remove=False)
        assert original == ["1.1.1.1/32"]
        assert new_list != original

    def test_enable_firewall_strips_open_ranges(self):
        new_list, changed, already = _apply_ip_to_allow_list(
            ["0.0.0.0/0", "::/0"], "2.2.2.2/32", remove=False, enable_firewall=True,
        )
        assert changed is True
        assert already is False
        assert new_list == ["2.2.2.2/32"]

    def test_enable_firewall_is_change_even_if_ip_present(self):
        """An open allow_list already containing the IP still changes: it locks down."""
        new_list, changed, already = _apply_ip_to_allow_list(
            ["2.2.2.2/32", "0.0.0.0/0"], "2.2.2.2/32", remove=False, enable_firewall=True,
        )
        assert changed is True
        assert already is False
        assert new_list == ["2.2.2.2/32"]

    def test_enable_firewall_noop_when_already_locked_down(self):
        _, changed, already = _apply_ip_to_allow_list(
            ["2.2.2.2/32"], "2.2.2.2/32", remove=False, enable_firewall=True,
        )
        assert changed is False
        assert already is True

    def test_enable_firewall_ignored_in_remove_mode(self):
        """--db-enable-firewall must not strip open ranges while removing an IP."""
        new_list, changed, _ = _apply_ip_to_allow_list(
            ["2.2.2.2/32", "0.0.0.0/0"], "2.2.2.2/32", remove=True, enable_firewall=True,
        )
        assert changed is True
        assert new_list == ["0.0.0.0/0"]


class TestUpdateAllDatabaseAcls:
    def _setup_common(self, monkeypatch, databases, ip="9.9.9.9"):
        """Configure common mocks for update_all_database_acls tests."""
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.databases.get_public_ip", mock.Mock(return_value=ip))
        monkeypatch.setattr("acc_fwu.databases.list_databases", mock.Mock(return_value=databases))

        put_mock = mock.Mock()
        monkeypatch.setattr("acc_fwu.databases.put_database_allow_list", put_mock)
        return put_mock

    def test_adds_ip_to_all_databases(self, monkeypatch, capsys):
        databases = [
            {"id": 1, "label": "primary", "engine": "mysql", "allow_list": []},
            {"id": 2, "label": "analytics", "engine": "postgresql",
             "allow_list": ["1.1.1.1/32"]},
        ]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=True)

        assert counts == {"changed": 2, "unchanged": 0, "skipped": 0, "failed": 0, "total": 2}
        assert put_mock.call_count == 2
        # First call: db id=1 mysql, allow_list should now contain the IP
        assert put_mock.call_args_list[0][0][0] == 1
        assert put_mock.call_args_list[0][0][1] == "mysql"
        assert "9.9.9.9/32" in put_mock.call_args_list[0][0][2]
        # Second call: db id=2 postgresql with both IPs
        assert put_mock.call_args_list[1][0][0] == 2
        assert put_mock.call_args_list[1][0][1] == "postgresql"
        assert "9.9.9.9/32" in put_mock.call_args_list[1][0][2]
        assert "1.1.1.1/32" in put_mock.call_args_list[1][0][2]

    def test_no_databases(self, monkeypatch, capsys):
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.databases.list_databases", mock.Mock(return_value=[]))
        monkeypatch.setattr("acc_fwu.databases.get_public_ip", mock.Mock(return_value="9.9.9.9"))

        counts = update_all_database_acls(quiet=False)

        assert counts["total"] == 0
        captured = capsys.readouterr()
        assert "No managed databases found" in captured.out

    def test_no_databases_implicit_is_silent(self, monkeypatch, capsys):
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.databases.list_databases", mock.Mock(return_value=[]))
        monkeypatch.setattr("acc_fwu.databases.get_public_ip", mock.Mock(return_value="9.9.9.9"))

        update_all_database_acls(quiet=False, implicit=True)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_ip_already_present_is_unchanged(self, monkeypatch, capsys):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": ["9.9.9.9/32"]}]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=False)

        assert counts["unchanged"] == 1
        assert counts["changed"] == 0
        put_mock.assert_not_called()
        captured = capsys.readouterr()
        assert "already present" in captured.out

    def test_remove_mode(self, monkeypatch):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": ["9.9.9.9/32", "1.1.1.1/32"]}]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=True, remove=True)

        assert counts["changed"] == 1
        sent = put_mock.call_args[0][2]
        assert sent == ["1.1.1.1/32"]

    def test_dry_run_does_not_call_put(self, monkeypatch, capsys):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": []}]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(dry_run=True)

        put_mock.assert_not_called()
        assert counts["changed"] == 1
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out

    def test_dry_run_respects_quiet(self, monkeypatch, capsys):
        """--dry-run with quiet=True should produce no output."""
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": []}]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(dry_run=True, quiet=True)

        put_mock.assert_not_called()
        assert counts["changed"] == 1
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_vpc_attached_database_is_skipped(self, monkeypatch, capsys):
        """Databases with a non-null private_network are skipped (regardless of engine)."""
        databases = [
            {"id": 1, "label": "vpc-mysql", "engine": "mysql",
             "allow_list": [], "private_network": {"vpc_id": 42, "subnet_id": 7},
             "vpc_id": 42, "public_access": False},
            {"id": 2, "label": "vpc-pg", "engine": "postgresql",
             "allow_list": [], "private_network": {"vpc_id": 99, "subnet_id": 3},
             "vpc_id": 99, "public_access": True},
            {"id": 3, "label": "public-mysql", "engine": "mysql",
             "allow_list": [], "private_network": None},
        ]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=False)

        assert counts["changed"] == 1
        assert counts["skipped"] == 2
        assert counts["failed"] == 0
        # Only the non-VPC database is updated
        put_mock.assert_called_once()
        assert put_mock.call_args[0][0] == 3
        # Skip notices are diagnostics and go to stderr
        captured = capsys.readouterr()
        assert "attached to VPC" in captured.err
        assert "vpc_id=42" in captured.err
        assert "vpc_id=99" in captured.err

    def test_vpc_skip_respects_quiet(self, monkeypatch, capsys):
        databases = [
            {"id": 1, "label": "vpc-db", "engine": "mysql",
             "allow_list": [], "private_network": {"vpc_id": 1}},
        ]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=True)

        assert counts["skipped"] == 1
        assert counts["failed"] == 0
        put_mock.assert_not_called()
        # Skips are expected conditions, so quiet silences them entirely
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_missing_private_network_field_treated_as_non_vpc(self, monkeypatch):
        """Older API responses without the private_network field should not be
        misclassified as VPC-attached."""
        databases = [
            {"id": 1, "label": "primary", "engine": "mysql", "allow_list": []},
        ]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=True)

        assert counts["changed"] == 1
        assert counts["failed"] == 0
        put_mock.assert_called_once()

    def test_unsupported_engine_is_skipped(self, monkeypatch, capsys):
        databases = [
            {"id": 1, "label": "redis", "engine": "redis", "allow_list": []},
            {"id": 2, "label": "primary", "engine": "mysql", "allow_list": []},
        ]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=False)

        assert counts["skipped"] == 1
        assert counts["failed"] == 0
        assert counts["changed"] == 1
        # Only the supported engine is updated
        put_mock.assert_called_once()
        assert put_mock.call_args[0][1] == "mysql"
        captured = capsys.readouterr()
        assert "unsupported engine" in captured.err

    def test_enable_firewall_strips_open_range(self, monkeypatch, capsys):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": ["0.0.0.0/0"]}]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=False, enable_firewall=True)

        assert counts["changed"] == 1
        sent = put_mock.call_args[0][2]
        assert "0.0.0.0/0" not in sent
        assert "9.9.9.9/32" in sent
        captured = capsys.readouterr()
        assert "Removed open range(s) (0.0.0.0/0)" in captured.out

    def test_enable_firewall_locks_down_even_when_ip_present(self, monkeypatch, capsys):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": ["9.9.9.9/32", "0.0.0.0/0", "::/0"]}]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=False, enable_firewall=True)

        assert counts["changed"] == 1
        put_mock.assert_called_once()
        sent = put_mock.call_args[0][2]
        assert sent == ["9.9.9.9/32"]
        captured = capsys.readouterr()
        # IP already present, so only the lockdown line, no "Added".
        assert "Removed open range(s) (0.0.0.0/0, ::/0)" in captured.out
        assert "Added" not in captured.out

    def test_enable_firewall_noop_without_open_ranges(self, monkeypatch):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": ["9.9.9.9/32"]}]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(quiet=True, enable_firewall=True)

        assert counts["unchanged"] == 1
        assert counts["changed"] == 0
        put_mock.assert_not_called()

    def test_enable_firewall_dry_run_does_not_put(self, monkeypatch, capsys):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": ["0.0.0.0/0"]}]
        put_mock = self._setup_common(monkeypatch, databases)

        counts = update_all_database_acls(dry_run=True, enable_firewall=True)

        put_mock.assert_not_called()
        assert counts["changed"] == 1
        captured = capsys.readouterr()
        assert "[DRY RUN] Would remove open range(s) (0.0.0.0/0)" in captured.out

    def test_put_failure_is_counted(self, monkeypatch, capsys):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": []}]
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.databases.list_databases", mock.Mock(return_value=databases))
        monkeypatch.setattr("acc_fwu.databases.get_public_ip", mock.Mock(return_value="9.9.9.9"))
        monkeypatch.setattr(
            "acc_fwu.databases.put_database_allow_list",
            mock.Mock(side_effect=requests.exceptions.HTTPError("500")),
        )

        counts = update_all_database_acls(quiet=False)

        assert counts["failed"] == 1
        assert counts["changed"] == 0
        captured = capsys.readouterr()
        assert "Error on mysql database 'primary' (ID: 1)" in captured.err
        assert "failed to update" in captured.err

    def test_summary_printed_when_not_quiet(self, monkeypatch, capsys):
        databases = [{"id": 1, "label": "primary", "engine": "mysql",
                      "allow_list": []}]
        self._setup_common(monkeypatch, databases)

        update_all_database_acls(quiet=False)

        captured = capsys.readouterr()
        assert "Done." in captured.out
        assert "changed=1" in captured.out

    def test_per_database_failure_does_not_abort_batch(self, monkeypatch, capsys):
        databases = [
            {"id": 1, "label": "primary", "engine": "mysql", "allow_list": []},
            {"id": 2, "label": "analytics", "engine": "postgresql", "allow_list": []},
        ]
        monkeypatch.setattr("acc_fwu.databases.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.databases.list_databases", mock.Mock(return_value=databases))
        monkeypatch.setattr("acc_fwu.databases.get_public_ip", mock.Mock(return_value="9.9.9.9"))

        def fake_put(database_id, engine, allow_list, headers=None, debug=False):
            if database_id == 1:
                raise requests.exceptions.HTTPError("500")

        monkeypatch.setattr("acc_fwu.databases.put_database_allow_list", fake_put)

        counts = update_all_database_acls(quiet=True)
        assert counts["changed"] == 1
        assert counts["failed"] == 1
        assert counts["total"] == 2
        # The failure is still reported on stderr despite quiet mode
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Error on mysql database 'primary' (ID: 1)" in captured.err
