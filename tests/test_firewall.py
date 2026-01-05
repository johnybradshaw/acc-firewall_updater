import pytest
import stat
from unittest import mock
import requests
from acc_fwu.firewall import (
    load_config, save_config, get_api_token, get_public_ip,
    remove_firewall_rule, update_firewall_rule, CONFIG_FILE_PATH, LINODE_CLI_CONFIG_PATH,
    validate_firewall_id, validate_label, validate_ip_address,
    list_firewalls, select_firewall
)
import os


class TestValidation:
    """Tests for input validation functions."""

    def test_validate_firewall_id_valid(self):
        assert validate_firewall_id("12345") is True
        assert validate_firewall_id("1") is True
        assert validate_firewall_id("999999999") is True

    def test_validate_firewall_id_invalid(self):
        with pytest.raises(ValueError, match="Invalid firewall ID"):
            validate_firewall_id("abc")
        with pytest.raises(ValueError, match="Invalid firewall ID"):
            validate_firewall_id("")
        with pytest.raises(ValueError, match="Invalid firewall ID"):
            validate_firewall_id("123abc")
        with pytest.raises(ValueError, match="Invalid firewall ID"):
            validate_firewall_id(None)

    def test_validate_label_valid(self):
        assert validate_label("Test-Label") is True
        assert validate_label("my_label") is True
        assert validate_label("Label123") is True
        assert validate_label("a") is True

    def test_validate_label_invalid(self):
        with pytest.raises(ValueError, match="Invalid label"):
            validate_label("")
        with pytest.raises(ValueError, match="Invalid label"):
            validate_label("label with spaces")
        with pytest.raises(ValueError, match="Invalid label"):
            validate_label("a" * 33)  # Too long
        with pytest.raises(ValueError, match="Invalid label"):
            validate_label("label@special!")

    def test_validate_ip_address_valid(self):
        assert validate_ip_address("192.168.1.1") is True
        assert validate_ip_address("10.0.0.1") is True
        assert validate_ip_address("255.255.255.255") is True
        assert validate_ip_address("0.0.0.0") is True

    def test_validate_ip_address_invalid(self):
        with pytest.raises(ValueError, match="Invalid IPv4 address"):
            validate_ip_address("256.1.1.1")
        with pytest.raises(ValueError, match="Invalid IPv4 address"):
            validate_ip_address("1.2.3")
        with pytest.raises(ValueError, match="Invalid IPv4 address"):
            validate_ip_address("not.an.ip")
        with pytest.raises(ValueError, match="Invalid IPv4 address"):
            validate_ip_address("")


class TestConfig:
    """Tests for configuration management functions."""

    def test_load_config(self, tmp_path, monkeypatch):
        # Create a temporary config file with the expected content
        config_file = tmp_path / ".acc-fwu-config"
        config_file.write_text("[DEFAULT]\nfirewall_id = 12345\nlabel = Test-Label\n")

        # Use monkeypatch to override CONFIG_FILE_PATH in the firewall module
        monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", str(config_file))

        # Now run the function and check the output
        firewall_id, label = load_config()
        assert firewall_id == "12345"
        assert label == "Test-Label"

    def test_load_config_without_label(self, tmp_path, monkeypatch):
        """Test loading config when label is missing (returns None)."""
        config_file = tmp_path / ".acc-fwu-config"
        config_file.write_text("[DEFAULT]\nfirewall_id = 12345\n")

        monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", str(config_file))

        firewall_id, label = load_config()
        assert firewall_id == "12345"
        assert label is None

    def test_load_config_file_not_found(self, monkeypatch):
        monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", "/non/existent/path")
        with pytest.raises(FileNotFoundError):
            load_config()

    def test_save_config(self, tmp_path, monkeypatch):
        config_file = tmp_path / ".acc-fwu-config"
        monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", str(config_file))

        save_config("12345", "Test-Label", quiet=True)

        saved_config = config_file.read_text()
        assert "firewall_id = 12345" in saved_config
        assert "label = Test-Label" in saved_config

    def test_save_config_prints_message_when_not_quiet(self, tmp_path, monkeypatch, capsys):
        """Test that save_config prints message when quiet=False."""
        config_file = tmp_path / ".acc-fwu-config"
        monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", str(config_file))

        save_config("12345", "Test-Label", quiet=False)

        captured = capsys.readouterr()
        assert "Configuration saved to" in captured.out

    def test_save_config_secure_permissions(self, tmp_path, monkeypatch):
        """Test that config file is created with secure permissions (600)."""
        config_file = tmp_path / ".acc-fwu-config"
        monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", str(config_file))

        save_config("12345", "Test-Label", quiet=True)

        # Check file permissions are owner read/write only (0600)
        file_stat = os.stat(config_file)
        file_mode = stat.S_IMODE(file_stat.st_mode)
        assert file_mode == stat.S_IRUSR | stat.S_IWUSR

    def test_save_config_validates_input(self, tmp_path, monkeypatch):
        """Test that save_config validates firewall_id and label."""
        config_file = tmp_path / ".acc-fwu-config"
        monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", str(config_file))

        with pytest.raises(ValueError, match="Invalid firewall ID"):
            save_config("invalid-id", "Test-Label")

        with pytest.raises(ValueError, match="Invalid label"):
            save_config("12345", "invalid label!")


class TestApiToken:
    """Tests for API token retrieval."""

    def test_get_api_token(self, monkeypatch, tmp_path):
        linode_config = """
        [DEFAULT]
        default-user = test-user

        [test-user]
        token = test-token
        """
        linode_cli_config_file = tmp_path / "linode-cli"
        linode_cli_config_file.write_text(linode_config)

        monkeypatch.setattr("acc_fwu.firewall.LINODE_CLI_CONFIG_PATH", str(linode_cli_config_file))

        token = get_api_token()
        assert token == "test-token"

    def test_get_api_token_file_not_found(self, monkeypatch):
        monkeypatch.setattr("acc_fwu.firewall.LINODE_CLI_CONFIG_PATH", "/non/existent/path")
        with pytest.raises(FileNotFoundError):
            get_api_token()

    def test_get_api_token_no_default_user(self, monkeypatch, tmp_path):
        """Test that missing default-user raises ValueError."""
        linode_config = """
        [DEFAULT]

        [some-user]
        token = test-token
        """
        linode_cli_config_file = tmp_path / "linode-cli"
        linode_cli_config_file.write_text(linode_config)

        monkeypatch.setattr("acc_fwu.firewall.LINODE_CLI_CONFIG_PATH", str(linode_cli_config_file))

        with pytest.raises(ValueError, match="No default user"):
            get_api_token()

    def test_get_api_token_no_token(self, monkeypatch, tmp_path):
        """Test that missing token raises ValueError."""
        linode_config = """
        [DEFAULT]
        default-user = test-user

        [test-user]
        region = us-east
        """
        linode_cli_config_file = tmp_path / "linode-cli"
        linode_cli_config_file.write_text(linode_config)

        monkeypatch.setattr("acc_fwu.firewall.LINODE_CLI_CONFIG_PATH", str(linode_cli_config_file))

        with pytest.raises(ValueError, match="No API token"):
            get_api_token()


class TestPublicIp:
    """Tests for public IP retrieval."""

    def test_get_public_ip(self, monkeypatch):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"ip": "192.168.1.100"}
        mock_response.raise_for_status = mock.Mock()
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))

        ip_address = get_public_ip()
        assert ip_address == "192.168.1.100"

    def test_get_public_ip_validates_response(self, monkeypatch):
        """Test that invalid IP from service raises ValueError."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"ip": "invalid"}
        mock_response.raise_for_status = mock.Mock()
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))

        with pytest.raises(ValueError, match="Invalid IPv4 address"):
            get_public_ip()


class TestRemoveFirewallRule:
    """Tests for remove_firewall_rule function."""

    def test_remove_firewall_rule(self, monkeypatch):
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [
                {"label": "Test-TCP", "protocol": "TCP"},
                {"label": "Test-UDP", "protocol": "UDP"},
            ]
        }
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        remove_firewall_rule("12345", "Test", quiet=True)

        requests.put.assert_called_once()
        call_args = requests.put.call_args[1]["json"]
        assert len(call_args["inbound"]) == 0

    def test_remove_firewall_rule_prints_success(self, monkeypatch, capsys):
        """Test that success message is printed when quiet=False."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [{"label": "Test-TCP", "protocol": "TCP"}]
        }
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        remove_firewall_rule("12345", "Test", quiet=False)

        captured = capsys.readouterr()
        assert "Removed" in captured.out
        assert "firewall rule" in captured.out

    def test_remove_firewall_rule_dry_run(self, monkeypatch, capsys):
        """Test that dry_run shows what would be done without making changes."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [
                {"label": "Test-TCP", "protocol": "TCP"},
            ]
        }
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock())
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        remove_firewall_rule("12345", "Test", dry_run=True)

        # PUT should not be called in dry_run mode
        requests.put.assert_not_called()
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out

    def test_remove_firewall_rule_no_matching_rules(self, monkeypatch, capsys):
        """Test when no rules match the label."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [{"label": "Other-TCP", "protocol": "TCP"}]
        }
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock())
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        remove_firewall_rule("12345", "Test", quiet=False)

        # PUT should not be called when no rules match
        requests.put.assert_not_called()
        captured = capsys.readouterr()
        assert "No rules found" in captured.out

    def test_remove_firewall_rule_no_matching_rules_quiet(self, monkeypatch, capsys):
        """Test quiet mode when no rules match."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [{"label": "Other-TCP", "protocol": "TCP"}]
        }
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock())
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        remove_firewall_rule("12345", "Test", quiet=True)

        # No output when quiet
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_remove_firewall_rule_with_debug(self, monkeypatch, capsys):
        """Test debug mode prints additional information."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [{"label": "Test-TCP", "protocol": "TCP"}]
        }
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        remove_firewall_rule("12345", "Test", debug=True, quiet=True)

        captured = capsys.readouterr()
        assert "Existing rules data before removal" in captured.out
        assert "Remaining rules data after removal" in captured.out

    def test_remove_firewall_rule_api_error_with_debug(self, monkeypatch, capsys):
        """Test debug output when API returns error."""
        mock_get_response = mock.Mock()
        mock_get_response.json.return_value = {
            "inbound": [{"label": "Test-TCP", "protocol": "TCP"}]
        }
        mock_get_response.raise_for_status = mock.Mock()

        mock_put_response = mock.Mock()
        mock_put_response.status_code = 400
        mock_put_response.content = b'{"errors": [{"reason": "Bad request"}]}'
        mock_put_response.raise_for_status = mock.Mock(
            side_effect=requests.exceptions.HTTPError("400 Bad Request")
        )

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_get_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        with pytest.raises(requests.exceptions.HTTPError):
            remove_firewall_rule("12345", "Test", debug=True)

        captured = capsys.readouterr()
        assert "Response status code: 400" in captured.out
        assert "Response content:" in captured.out

    def test_remove_firewall_rule_validates_input(self, monkeypatch):
        """Test that remove_firewall_rule validates inputs before API calls."""
        with pytest.raises(ValueError, match="Invalid firewall ID"):
            remove_firewall_rule("invalid", "Test")

        with pytest.raises(ValueError, match="Invalid label"):
            remove_firewall_rule("12345", "invalid label!")


class TestUpdateFirewallRule:
    """Tests for update_firewall_rule function."""

    def test_update_firewall_rule_creates_new_rules(self, monkeypatch):
        """Test creating new rules when none exist."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"inbound": []}
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", quiet=True)

        requests.put.assert_called_once()
        call_args = requests.put.call_args[1]["json"]
        assert len(call_args["inbound"]) == 3  # TCP, UDP, ICMP

    def test_update_firewall_rule_updates_existing_rules(self, monkeypatch, capsys):
        """Test updating existing rules instead of creating new ones."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [
                {"label": "Test-TCP", "protocol": "TCP", "addresses": {"ipv4": ["10.0.0.1/32"]}},
                {"label": "Test-UDP", "protocol": "UDP", "addresses": {"ipv4": ["10.0.0.1/32"]}},
                {"label": "Test-ICMP", "protocol": "ICMP", "addresses": {"ipv4": ["10.0.0.1/32"]}},
            ]
        }
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", quiet=True)

        requests.put.assert_called_once()
        call_args = requests.put.call_args[1]["json"]
        # Should still have 3 rules, but with updated IP
        assert len(call_args["inbound"]) == 3
        for rule in call_args["inbound"]:
            assert rule["addresses"]["ipv4"] == ["192.168.1.100/32"]

    def test_update_firewall_rule_prints_success(self, monkeypatch, capsys):
        """Test that success message is printed when quiet=False."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"inbound": []}
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", quiet=False)

        captured = capsys.readouterr()
        assert "Created/updated firewall rules" in captured.out
        assert "192.168.1.100/32" in captured.out

    def test_update_firewall_rule_dry_run(self, monkeypatch, capsys):
        """Test that dry_run shows what would be done without making changes."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"inbound": []}
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock())
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", dry_run=True)

        # PUT should not be called in dry_run mode
        requests.put.assert_not_called()
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out

    def test_update_firewall_rule_dry_run_with_existing_rules(self, monkeypatch, capsys):
        """Test dry_run correctly reports updates vs creates."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [
                {"label": "Test-TCP", "protocol": "TCP", "addresses": {"ipv4": ["10.0.0.1/32"]}},
            ]
        }
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock())
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", dry_run=True)

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "update 1" in captured.out
        assert "create 2" in captured.out

    def test_update_firewall_rule_with_debug(self, monkeypatch, capsys):
        """Test debug mode prints additional information."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"inbound": []}
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", debug=True, quiet=True)

        captured = capsys.readouterr()
        assert "Existing rules data:" in captured.out

    def test_update_firewall_rule_api_error_with_debug(self, monkeypatch, capsys):
        """Test debug output when API returns error."""
        mock_get_response = mock.Mock()
        mock_get_response.json.return_value = {"inbound": []}
        mock_get_response.raise_for_status = mock.Mock()

        mock_put_response = mock.Mock()
        mock_put_response.status_code = 400
        mock_put_response.content = b'{"errors": [{"reason": "Bad request"}]}'
        mock_put_response.raise_for_status = mock.Mock(
            side_effect=requests.exceptions.HTTPError("400 Bad Request")
        )

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_get_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        with pytest.raises(requests.exceptions.HTTPError):
            update_firewall_rule("12345", "Test", debug=True)

        captured = capsys.readouterr()
        assert "Response status code: 400" in captured.out
        assert "Response content:" in captured.out

    def test_update_firewall_rule_validates_input(self, monkeypatch):
        """Test that update_firewall_rule validates inputs before API calls."""
        with pytest.raises(ValueError, match="Invalid firewall ID"):
            update_firewall_rule("invalid", "Test")

        with pytest.raises(ValueError, match="Invalid label"):
            update_firewall_rule("12345", "invalid label!")

    def test_update_firewall_rule_add_ip_mode(self, monkeypatch):
        """Test add_ip mode appends IP instead of replacing."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [
                {"label": "Test-TCP", "protocol": "TCP", "addresses": {"ipv4": ["10.0.0.1/32"]}},
                {"label": "Test-UDP", "protocol": "UDP", "addresses": {"ipv4": ["10.0.0.1/32"]}},
                {"label": "Test-ICMP", "protocol": "ICMP", "addresses": {"ipv4": ["10.0.0.1/32"]}},
            ]
        }
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", quiet=True, add_ip=True)

        requests.put.assert_called_once()
        call_args = requests.put.call_args[1]["json"]
        # Should have both IPs in each rule
        for rule in call_args["inbound"]:
            if rule["label"].startswith("Test-"):
                assert "10.0.0.1/32" in rule["addresses"]["ipv4"]
                assert "192.168.1.100/32" in rule["addresses"]["ipv4"]

    def test_update_firewall_rule_add_ip_already_exists(self, monkeypatch, capsys):
        """Test add_ip mode when IP already exists."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [
                {"label": "Test-TCP", "protocol": "TCP", "addresses": {"ipv4": ["192.168.1.100/32"]}},
                {"label": "Test-UDP", "protocol": "UDP", "addresses": {"ipv4": ["192.168.1.100/32"]}},
                {"label": "Test-ICMP", "protocol": "ICMP", "addresses": {"ipv4": ["192.168.1.100/32"]}},
            ]
        }
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock())
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", quiet=False, add_ip=True)

        # PUT should not be called when IP already exists
        requests.put.assert_not_called()
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_update_firewall_rule_add_ip_dry_run(self, monkeypatch, capsys):
        """Test add_ip mode with dry_run."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "inbound": [
                {"label": "Test-TCP", "protocol": "TCP", "addresses": {"ipv4": ["10.0.0.1/32"]}},
            ]
        }
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock())
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", dry_run=True, add_ip=True)

        requests.put.assert_not_called()
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "add to" in captured.out

    def test_update_firewall_rule_add_ip_creates_new_rules(self, monkeypatch):
        """Test add_ip mode creates new rules if they don't exist."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"inbound": []}
        mock_response.raise_for_status = mock.Mock()
        mock_put_response = mock.Mock()
        mock_put_response.status_code = 200

        monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock.Mock(return_value="192.168.1.100"))
        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr(requests, "put", mock.Mock(return_value=mock_put_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        update_firewall_rule("12345", "Test", quiet=True, add_ip=True)

        requests.put.assert_called_once()
        call_args = requests.put.call_args[1]["json"]
        assert len(call_args["inbound"]) == 3  # TCP, UDP, ICMP


class TestListFirewalls:
    """Tests for list_firewalls function."""

    def test_list_firewalls_success(self, monkeypatch):
        """Test successful listing of firewalls."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": 12345, "label": "my-firewall", "status": "enabled"},
                {"id": 67890, "label": "another-firewall", "status": "disabled"},
            ]
        }
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        firewalls = list_firewalls()

        assert len(firewalls) == 2
        assert firewalls[0]["id"] == 12345
        assert firewalls[0]["label"] == "my-firewall"
        assert firewalls[0]["status"] == "enabled"
        assert firewalls[1]["id"] == 67890

    def test_list_firewalls_empty(self, monkeypatch):
        """Test listing when no firewalls exist."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        firewalls = list_firewalls()

        assert len(firewalls) == 0

    def test_list_firewalls_api_error(self, monkeypatch):
        """Test handling of API errors."""
        mock_response = mock.Mock()
        mock_response.raise_for_status = mock.Mock(
            side_effect=requests.exceptions.HTTPError("401 Unauthorized")
        )

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        with pytest.raises(requests.exceptions.HTTPError):
            list_firewalls()

    def test_list_firewalls_missing_label(self, monkeypatch):
        """Test handling of firewalls with missing labels."""
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": 12345, "status": "enabled"},  # No label
            ]
        }
        mock_response.raise_for_status = mock.Mock()

        monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
        monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock.Mock(return_value="test-token"))

        firewalls = list_firewalls()

        assert len(firewalls) == 1
        assert firewalls[0]["label"] == ""


class TestSelectFirewall:
    """Tests for select_firewall function."""

    def test_select_firewall_success(self, monkeypatch, capsys):
        """Test successful firewall selection."""
        mock_list = mock.Mock(return_value=[
            {"id": 12345, "label": "my-firewall", "status": "enabled"},
            {"id": 67890, "label": "another-firewall", "status": "disabled"},
        ])
        monkeypatch.setattr("acc_fwu.firewall.list_firewalls", mock_list)
        monkeypatch.setattr("builtins.input", mock.Mock(return_value="1"))

        firewall_id = select_firewall()

        assert firewall_id == "12345"
        captured = capsys.readouterr()
        assert "Available firewalls" in captured.out
        assert "my-firewall" in captured.out

    def test_select_firewall_second_option(self, monkeypatch, capsys):
        """Test selecting second firewall."""
        mock_list = mock.Mock(return_value=[
            {"id": 12345, "label": "my-firewall", "status": "enabled"},
            {"id": 67890, "label": "another-firewall", "status": "disabled"},
        ])
        monkeypatch.setattr("acc_fwu.firewall.list_firewalls", mock_list)
        monkeypatch.setattr("builtins.input", mock.Mock(return_value="2"))

        firewall_id = select_firewall()

        assert firewall_id == "67890"
        captured = capsys.readouterr()
        assert "another-firewall" in captured.out

    def test_select_firewall_no_firewalls(self, monkeypatch):
        """Test error when no firewalls available."""
        mock_list = mock.Mock(return_value=[])
        monkeypatch.setattr("acc_fwu.firewall.list_firewalls", mock_list)

        with pytest.raises(ValueError, match="No firewalls found"):
            select_firewall()

    def test_select_firewall_invalid_input_retry(self, monkeypatch, capsys):
        """Test retry on invalid input."""
        mock_list = mock.Mock(return_value=[
            {"id": 12345, "label": "my-firewall", "status": "enabled"},
        ])
        monkeypatch.setattr("acc_fwu.firewall.list_firewalls", mock_list)
        # First invalid input, then valid
        inputs = iter(["abc", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        firewall_id = select_firewall()

        assert firewall_id == "12345"
        captured = capsys.readouterr()
        assert "valid number" in captured.out

    def test_select_firewall_out_of_range_retry(self, monkeypatch, capsys):
        """Test retry on out of range input."""
        mock_list = mock.Mock(return_value=[
            {"id": 12345, "label": "my-firewall", "status": "enabled"},
        ])
        monkeypatch.setattr("acc_fwu.firewall.list_firewalls", mock_list)
        # First out of range, then valid
        inputs = iter(["5", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        firewall_id = select_firewall()

        assert firewall_id == "12345"
        captured = capsys.readouterr()
        assert "between 1 and" in captured.out

    def test_select_firewall_keyboard_interrupt(self, monkeypatch):
        """Test handling of keyboard interrupt."""
        mock_list = mock.Mock(return_value=[
            {"id": 12345, "label": "my-firewall", "status": "enabled"},
        ])
        monkeypatch.setattr("acc_fwu.firewall.list_firewalls", mock_list)
        monkeypatch.setattr("builtins.input", mock.Mock(side_effect=KeyboardInterrupt))

        with pytest.raises(ValueError, match="cancelled"):
            select_firewall()

    def test_select_firewall_eof(self, monkeypatch):
        """Test handling of EOF (e.g., piped input ends)."""
        mock_list = mock.Mock(return_value=[
            {"id": 12345, "label": "my-firewall", "status": "enabled"},
        ])
        monkeypatch.setattr("acc_fwu.firewall.list_firewalls", mock_list)
        monkeypatch.setattr("builtins.input", mock.Mock(side_effect=EOFError))

        with pytest.raises(ValueError, match="cancelled"):
            select_firewall()

    def test_select_firewall_quiet_mode_error(self, monkeypatch):
        """Test that quiet mode raises error (interactive selection not possible)."""
        with pytest.raises(ValueError, match="Cannot select firewall interactively in quiet mode"):
            select_firewall(quiet=True)
