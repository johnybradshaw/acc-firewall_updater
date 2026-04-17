import pytest
import requests
from unittest import mock

from acc_fwu.lke import (
    LINODE_LKE_BASE_URL,
    _apply_ip_to_acl,
    get_lke_acl,
    list_lke_clusters,
    put_lke_acl,
    update_all_lke_acls,
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


class TestListLkeClusters:
    def test_returns_clusters_with_tier(self, monkeypatch):
        resp = _mock_response({
            "data": [
                {"id": 1, "label": "std", "region": "us-east",
                 "k8s_version": "1.30", "tier": "standard", "status": "ready"},
                {"id": 2, "label": "ent", "region": "eu-west",
                 "k8s_version": "1.30", "tier": "enterprise", "status": "ready"},
            ],
            "pages": 1,
        })
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=resp))
        monkeypatch.setattr("acc_fwu.lke.get_api_token", mock.Mock(return_value="test-token"))

        clusters = list_lke_clusters()
        assert len(clusters) == 2
        assert clusters[0]["tier"] == "standard"
        assert clusters[1]["tier"] == "enterprise"

    def test_pagination(self, monkeypatch):
        page1 = _mock_response({
            "data": [{"id": 1, "label": "a", "region": "us", "tier": "standard"}],
            "pages": 2,
        })
        page2 = _mock_response({
            "data": [{"id": 2, "label": "b", "region": "us", "tier": "enterprise"}],
            "pages": 2,
        })
        mock_get = mock.Mock(side_effect=[page1, page2])
        monkeypatch.setattr(requests, "get", mock_get)
        monkeypatch.setattr("acc_fwu.lke.get_api_token", mock.Mock(return_value="test-token"))

        clusters = list_lke_clusters()
        assert [c["id"] for c in clusters] == [1, 2]
        assert mock_get.call_args_list[0][1]["params"] == {"page": 1, "page_size": LINODE_API_PAGE_SIZE}
        assert mock_get.call_args_list[1][1]["params"] == {"page": 2, "page_size": LINODE_API_PAGE_SIZE}

    def test_defaults_tier_when_missing(self, monkeypatch):
        resp = _mock_response({"data": [{"id": 1}], "pages": 1})
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=resp))
        monkeypatch.setattr("acc_fwu.lke.get_api_token", mock.Mock(return_value="test-token"))

        clusters = list_lke_clusters()
        assert clusters[0]["tier"] == "standard"
        assert clusters[0]["label"] == ""


class TestGetLkeAcl:
    def test_returns_normalized_acl(self, monkeypatch):
        resp = _mock_response({
            "acl": {"enabled": True, "addresses": {"ipv4": ["1.2.3.4/32"], "ipv6": []}}
        })
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=resp))

        acl = get_lke_acl(42, headers=HEADERS)
        assert acl["enabled"] is True
        assert acl["addresses"]["ipv4"] == ["1.2.3.4/32"]
        assert acl["addresses"]["ipv6"] == []

    def test_handles_missing_acl(self, monkeypatch):
        resp = _mock_response({})
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=resp))

        acl = get_lke_acl(42, headers=HEADERS)
        assert acl == {"enabled": False, "addresses": {"ipv4": [], "ipv6": []}}

    def test_handles_null_addresses(self, monkeypatch):
        resp = _mock_response({"acl": {"enabled": False, "addresses": None}})
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=resp))

        acl = get_lke_acl(42, headers=HEADERS)
        assert acl["addresses"] == {"ipv4": [], "ipv6": []}


class TestPutLkeAcl:
    def test_sends_acl_envelope(self, monkeypatch):
        resp = _mock_response(status_code=200)
        mock_put = mock.Mock(return_value=resp)
        monkeypatch.setattr(requests, "put", mock_put)

        body = {"enabled": True, "addresses": {"ipv4": ["1.2.3.4/32"], "ipv6": []}}
        put_lke_acl(42, body, headers=HEADERS)

        assert mock_put.call_count == 1
        assert mock_put.call_args[0][0] == f"{LINODE_LKE_BASE_URL}/42/control_plane_acl"
        assert mock_put.call_args[1]["json"] == {"acl": body}

    def test_raises_on_error_status(self, monkeypatch):
        resp = _mock_response(
            status_code=400,
            raise_exc=requests.exceptions.HTTPError("400"),
        )
        resp.content = b'{"errors": [{"reason": "bad"}]}'
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=resp))

        with pytest.raises(requests.exceptions.HTTPError):
            put_lke_acl(42, {"enabled": True, "addresses": {"ipv4": [], "ipv6": []}},
                        headers=HEADERS, debug=True)


class TestApplyIpToAcl:
    def test_add_when_absent_adds(self):
        acl = {"enabled": True, "addresses": {"ipv4": ["1.1.1.1/32"], "ipv6": []}}
        new_acl, changed, already = _apply_ip_to_acl(acl, "2.2.2.2/32", remove=False)
        assert changed is True
        assert already is False
        assert "2.2.2.2/32" in new_acl["addresses"]["ipv4"]
        assert "1.1.1.1/32" in new_acl["addresses"]["ipv4"]

    def test_add_when_present_noop(self):
        acl = {"enabled": True, "addresses": {"ipv4": ["2.2.2.2/32"], "ipv6": []}}
        _, changed, already = _apply_ip_to_acl(acl, "2.2.2.2/32", remove=False)
        assert changed is False
        assert already is True

    def test_remove_when_present_removes(self):
        acl = {"enabled": True, "addresses": {"ipv4": ["2.2.2.2/32"], "ipv6": []}}
        new_acl, changed, already = _apply_ip_to_acl(acl, "2.2.2.2/32", remove=True)
        assert changed is True
        assert already is False
        assert "2.2.2.2/32" not in new_acl["addresses"]["ipv4"]

    def test_remove_when_absent_noop(self):
        acl = {"enabled": True, "addresses": {"ipv4": ["1.1.1.1/32"], "ipv6": []}}
        _, changed, already = _apply_ip_to_acl(acl, "2.2.2.2/32", remove=True)
        assert changed is False
        assert already is True

    def test_preserves_enabled_and_ipv6(self):
        acl = {"enabled": False, "addresses": {"ipv4": [], "ipv6": ["::/0"]}}
        new_acl, _, _ = _apply_ip_to_acl(acl, "2.2.2.2/32", remove=False)
        assert new_acl["enabled"] is False
        assert new_acl["addresses"]["ipv6"] == ["::/0"]


class TestUpdateAllLkeAcls:
    def _setup_common(self, monkeypatch, clusters, acls_by_id, ip="9.9.9.9"):
        """Configure common mocks for update_all_lke_acls tests."""
        monkeypatch.setattr("acc_fwu.lke.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.lke.get_public_ip", mock.Mock(return_value=ip))
        monkeypatch.setattr("acc_fwu.lke.list_lke_clusters", mock.Mock(return_value=clusters))

        def fake_get_acl(cluster_id, headers=None):
            return acls_by_id[cluster_id]
        monkeypatch.setattr("acc_fwu.lke.get_lke_acl", fake_get_acl)

        put_mock = mock.Mock()
        monkeypatch.setattr("acc_fwu.lke.put_lke_acl", put_mock)
        return put_mock

    def test_adds_ip_to_all_clusters(self, monkeypatch, capsys):
        clusters = [
            {"id": 1, "label": "std", "tier": "standard"},
            {"id": 2, "label": "ent", "tier": "enterprise"},
        ]
        acls = {
            1: {"enabled": True, "addresses": {"ipv4": [], "ipv6": []}},
            2: {"enabled": True, "addresses": {"ipv4": ["1.1.1.1/32"], "ipv6": []}},
        }
        put_mock = self._setup_common(monkeypatch, clusters, acls)

        counts = update_all_lke_acls(quiet=True)

        assert counts == {"changed": 2, "unchanged": 0, "failed": 0, "total": 2}
        assert put_mock.call_count == 2
        sent = put_mock.call_args_list[0][0][1]
        assert "9.9.9.9/32" in sent["addresses"]["ipv4"]

    def test_no_clusters(self, monkeypatch, capsys):
        monkeypatch.setattr("acc_fwu.lke.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.lke.list_lke_clusters", mock.Mock(return_value=[]))
        monkeypatch.setattr("acc_fwu.lke.get_public_ip", mock.Mock(return_value="9.9.9.9"))

        counts = update_all_lke_acls(quiet=False)

        assert counts["total"] == 0
        captured = capsys.readouterr()
        assert "No LKE clusters found" in captured.out

    def test_ip_already_present_is_unchanged(self, monkeypatch, capsys):
        clusters = [{"id": 1, "label": "std", "tier": "standard"}]
        acls = {1: {"enabled": True, "addresses": {"ipv4": ["9.9.9.9/32"], "ipv6": []}}}
        put_mock = self._setup_common(monkeypatch, clusters, acls)

        counts = update_all_lke_acls(quiet=False)

        assert counts["unchanged"] == 1
        assert counts["changed"] == 0
        put_mock.assert_not_called()
        captured = capsys.readouterr()
        assert "already present" in captured.out

    def test_remove_mode(self, monkeypatch):
        clusters = [{"id": 1, "label": "std", "tier": "standard"}]
        acls = {1: {"enabled": True, "addresses": {"ipv4": ["9.9.9.9/32", "1.1.1.1/32"], "ipv6": []}}}
        put_mock = self._setup_common(monkeypatch, clusters, acls)

        counts = update_all_lke_acls(quiet=True, remove=True)

        assert counts["changed"] == 1
        sent = put_mock.call_args[0][1]
        assert sent["addresses"]["ipv4"] == ["1.1.1.1/32"]

    def test_dry_run_does_not_call_put(self, monkeypatch, capsys):
        clusters = [{"id": 1, "label": "std", "tier": "standard"}]
        acls = {1: {"enabled": True, "addresses": {"ipv4": [], "ipv6": []}}}
        put_mock = self._setup_common(monkeypatch, clusters, acls)

        counts = update_all_lke_acls(dry_run=True)

        put_mock.assert_not_called()
        assert counts["changed"] == 1
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out

    def test_disabled_acl_warning_when_adding(self, monkeypatch, capsys):
        clusters = [{"id": 1, "label": "std", "tier": "standard"}]
        acls = {1: {"enabled": False, "addresses": {"ipv4": [], "ipv6": []}}}
        self._setup_common(monkeypatch, clusters, acls)

        update_all_lke_acls(quiet=False)

        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "disabled" in captured.out

    def test_get_acl_failure_is_counted(self, monkeypatch, capsys):
        clusters = [
            {"id": 1, "label": "ok", "tier": "standard"},
            {"id": 2, "label": "fail", "tier": "standard"},
        ]
        acls = {1: {"enabled": True, "addresses": {"ipv4": [], "ipv6": []}}}

        def fake_get_acl(cluster_id, headers=None):
            if cluster_id == 2:
                raise requests.exceptions.HTTPError("500")
            return acls[cluster_id]

        monkeypatch.setattr("acc_fwu.lke.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.lke.list_lke_clusters", mock.Mock(return_value=clusters))
        monkeypatch.setattr("acc_fwu.lke.get_public_ip", mock.Mock(return_value="9.9.9.9"))
        monkeypatch.setattr("acc_fwu.lke.get_lke_acl", fake_get_acl)
        put_mock = mock.Mock()
        monkeypatch.setattr("acc_fwu.lke.put_lke_acl", put_mock)

        counts = update_all_lke_acls(quiet=False)

        assert counts["changed"] == 1
        assert counts["failed"] == 1
        put_mock.assert_called_once()

    def test_put_failure_is_counted(self, monkeypatch):
        clusters = [{"id": 1, "label": "std", "tier": "standard"}]
        acls = {1: {"enabled": True, "addresses": {"ipv4": [], "ipv6": []}}}
        monkeypatch.setattr("acc_fwu.lke.get_api_token", mock.Mock(return_value="test-token"))
        monkeypatch.setattr("acc_fwu.lke.list_lke_clusters", mock.Mock(return_value=clusters))
        monkeypatch.setattr("acc_fwu.lke.get_public_ip", mock.Mock(return_value="9.9.9.9"))
        monkeypatch.setattr("acc_fwu.lke.get_lke_acl", lambda cid, headers=None: acls[cid])
        monkeypatch.setattr(
            "acc_fwu.lke.put_lke_acl",
            mock.Mock(side_effect=requests.exceptions.HTTPError("500")),
        )

        counts = update_all_lke_acls(quiet=True)

        assert counts["failed"] == 1
        assert counts["changed"] == 0
