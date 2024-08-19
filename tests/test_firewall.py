import pytest
from unittest import mock
import requests
from acc_fwu.firewall import (
    load_config, save_config, get_api_token, get_public_ip,
    remove_firewall_rule, update_firewall_rule, CONFIG_FILE_PATH, LINODE_CLI_CONFIG_PATH
)
import os

def test_load_config(tmp_path, monkeypatch):
    # Create a temporary config file with the expected content
    config_file = tmp_path / ".acc-fwu-config"
    config_file.write_text("[DEFAULT]\nfirewall_id = 12345\nlabel = Test-Label\n")
    
    # Correctly reference CONFIG_FILE_PATH in the acc_fwu.firewall module
    print("Testing CONFIG_FILE_PATH:", str(config_file))

    # Use monkeypatch to override CONFIG_FILE_PATH in the firewall module
    monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", str(config_file))

    # Now run the function and check the output
    firewall_id, label = load_config()
    assert firewall_id == "12345"
    assert label == "Test-Label"

def test_load_config_file_not_found(monkeypatch):
    # Correctly reference CONFIG_FILE_PATH in the acc_fwu.firewall module
    monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", "/non/existent/path")
    with pytest.raises(FileNotFoundError):
        load_config()

def test_save_config(tmp_path, monkeypatch):
    config_file = tmp_path / ".acc-fwu-config"
    monkeypatch.setattr("acc_fwu.firewall.CONFIG_FILE_PATH", str(config_file))

    save_config("12345", "Test-Label")
    
    saved_config = config_file.read_text()
    assert "firewall_id = 12345" in saved_config
    assert "label = Test-Label" in saved_config

def test_get_api_token(monkeypatch, tmp_path):
    # Mock content of the Linode CLI configuration file
    linode_config = """
    [DEFAULT]
    default-user = test-user

    [test-user]
    token = test-token
    """
    # Create a temporary configuration file
    linode_cli_config_file = tmp_path / "linode-cli"
    linode_cli_config_file.write_text(linode_config)

    # Ensure LINODE_CLI_CONFIG_PATH is correctly patched to use the temp file
    monkeypatch.setattr("acc_fwu.firewall.LINODE_CLI_CONFIG_PATH", str(linode_cli_config_file))
    
    # Call the function to get the API token
    token = get_api_token()
    
    # Assert that the correct token was returned
    assert token == "test-token"

def test_get_api_token_file_not_found(monkeypatch):
    # Ensure LINODE_CLI_CONFIG_PATH is pointing to a mock or non-existent path
    monkeypatch.setattr("acc_fwu.firewall.LINODE_CLI_CONFIG_PATH", "/non/existent/path")

    # Call the function to get the API token
    with pytest.raises(FileNotFoundError):
        get_api_token()

def test_get_public_ip(monkeypatch):
    mock_response = mock.Mock()
    mock_response.json.return_value = {"ip": "123.456.789.000"}
    monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))

    ip_address = get_public_ip()
    assert ip_address == "123.456.789.000"

def test_remove_firewall_rule(monkeypatch):
    mock_response = mock.Mock()
    mock_response.json.return_value = {
        "inbound": [
            {"label": "Test-TCP", "protocol": "TCP"},
            {"label": "Test-UDP", "protocol": "UDP"},
        ]
    }
    monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
    monkeypatch.setattr(requests, "put", mock.Mock())

    mock_get_api_token = mock.Mock(return_value="test-token")
    monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock_get_api_token)

    remove_firewall_rule("12345", "Test")

    requests.put.assert_called_once()
    call_args = requests.put.call_args[1]["json"]
    assert len(call_args["inbound"]) == 0  # Rules should have been removed

def test_update_firewall_rule(monkeypatch):
    mock_get_ip = mock.Mock(return_value="123.456.789.000")
    mock_response = mock.Mock()
    mock_response.json.return_value = {
        "inbound": []
    }
    monkeypatch.setattr("acc_fwu.firewall.get_public_ip", mock_get_ip)
    monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))
    monkeypatch.setattr(requests, "put", mock.Mock())

    mock_get_api_token = mock.Mock(return_value="test-token")
    monkeypatch.setattr("acc_fwu.firewall.get_api_token", mock_get_api_token)

    update_firewall_rule("12345", "Test")

    requests.put.assert_called_once()
    call_args = requests.put.call_args[1]["json"]
    assert len(call_args["inbound"]) == 3  # Three protocols: TCP, UDP, ICMP