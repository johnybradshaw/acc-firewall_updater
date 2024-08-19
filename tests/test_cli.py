import pytest
from unittest import mock
import sys
from acc_fwu.cli import main

def test_main_with_firewall_id_and_label(monkeypatch):
    # Mock the functions that interact with the file system or network
    mock_save_config = mock.MagicMock()
    mock_update_firewall_rule = mock.MagicMock()

    # Use monkeypatch to replace these functions in the module
    monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
    monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)

    # Simulate command-line arguments
    monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '--label', 'Test-Label'])

    # Run the main function
    main()

    # Check that the correct functions were called with the expected arguments
    mock_save_config.assert_called_once_with("12345", "Test-Label")
    mock_update_firewall_rule.assert_called_once_with("12345", "Test-Label", debug=False)

def test_main_without_firewall_id(monkeypatch):
    # Mock the functions that interact with the file system or network
    mock_load_config = mock.MagicMock(return_value=("12345", "Loaded-Label"))
    mock_update_firewall_rule = mock.MagicMock()

    # Use monkeypatch to replace these functions in the module
    monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
    monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)

    # Simulate command-line arguments without --firewall_id
    monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

    # Run the main function
    main()

    # Check that the correct functions were called with the expected arguments
    mock_load_config.assert_called_once()
    mock_update_firewall_rule.assert_called_once_with("12345", "Loaded-Label", debug=False)

def test_main_without_config_file(monkeypatch):
    # Mock load_config to raise a FileNotFoundError
    mock_load_config = mock.MagicMock(side_effect=FileNotFoundError)
    mock_print = mock.MagicMock()

    # Use monkeypatch to replace these functions in the module
    monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
    monkeypatch.setattr("builtins.print", mock_print)

    # Simulate command-line arguments without --firewall_id
    monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

    # Run the main function
    main()

    # Check that load_config was called and the appropriate error message was printed
    mock_load_config.assert_called_once()
    mock_print.assert_called_once_with("No configuration file found. Please run the script with --firewall_id (and optionally --label) to create the config file.")

def test_main_with_remove_flag(monkeypatch):
    # Mock the functions that interact with the file system or network
    mock_save_config = mock.MagicMock()
    mock_remove_firewall_rule = mock.MagicMock()

    # Use monkeypatch to replace these functions in the module
    monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
    monkeypatch.setattr("acc_fwu.cli.remove_firewall_rule", mock_remove_firewall_rule)

    # Simulate command-line arguments with the --remove flag
    monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '--label', 'Test-Label', '-r'])

    # Run the main function
    main()

    # Check that the correct functions were called with the expected arguments
    mock_save_config.assert_called_once_with("12345", "Test-Label")
    mock_remove_firewall_rule.assert_called_once_with("12345", "Test-Label", debug=False)