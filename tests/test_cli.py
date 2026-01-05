import pytest
from unittest import mock
import sys
from acc_fwu.cli import main


class TestCliBasicOperations:
    """Tests for basic CLI operations."""

    def test_main_with_firewall_id_and_label(self, monkeypatch):
        """Test CLI with firewall_id and label arguments."""
        mock_save_config = mock.MagicMock()
        mock_update_firewall_rule = mock.MagicMock()
        mock_validate_firewall_id = mock.MagicMock(return_value=True)
        mock_validate_label = mock.MagicMock(return_value=True)

        monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)
        monkeypatch.setattr("acc_fwu.cli.validate_firewall_id", mock_validate_firewall_id)
        monkeypatch.setattr("acc_fwu.cli.validate_label", mock_validate_label)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '--label', 'Test-Label'])

        main()

        mock_save_config.assert_called_once_with("12345", "Test-Label", quiet=False)
        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Test-Label", debug=False, quiet=False, dry_run=False, add_ip=False
        )

    def test_main_without_firewall_id(self, monkeypatch):
        """Test CLI loads config when firewall_id not provided."""
        mock_load_config = mock.MagicMock(return_value=("12345", "Loaded-Label"))
        mock_update_firewall_rule = mock.MagicMock()

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

        main()

        mock_load_config.assert_called_once()
        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Loaded-Label", debug=False, quiet=False, dry_run=False, add_ip=False
        )

    def test_main_without_config_file(self, monkeypatch):
        """Test CLI handles missing config file gracefully."""
        mock_load_config = mock.MagicMock(side_effect=FileNotFoundError)

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_load_config.assert_called_once()

    def test_main_config_without_label_uses_default(self, monkeypatch):
        """Test CLI uses default label when config has None for label."""
        mock_load_config = mock.MagicMock(return_value=("12345", None))
        mock_update_firewall_rule = mock.MagicMock()

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

        main()

        mock_load_config.assert_called_once()
        # Should use the default label "Default-Label"
        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Default-Label", debug=False, quiet=False, dry_run=False, add_ip=False
        )


class TestCliRemoveOperation:
    """Tests for the --remove flag."""

    def test_main_with_remove_flag(self, monkeypatch):
        """Test CLI with --remove flag."""
        mock_save_config = mock.MagicMock()
        mock_remove_firewall_rule = mock.MagicMock()
        mock_validate_firewall_id = mock.MagicMock(return_value=True)
        mock_validate_label = mock.MagicMock(return_value=True)

        monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
        monkeypatch.setattr("acc_fwu.cli.remove_firewall_rule", mock_remove_firewall_rule)
        monkeypatch.setattr("acc_fwu.cli.validate_firewall_id", mock_validate_firewall_id)
        monkeypatch.setattr("acc_fwu.cli.validate_label", mock_validate_label)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '--label', 'Test-Label', '-r'])

        main()

        mock_save_config.assert_called_once_with("12345", "Test-Label", quiet=False)
        mock_remove_firewall_rule.assert_called_once_with(
            "12345", "Test-Label", debug=False, quiet=False, dry_run=False
        )


class TestCliNewOptions:
    """Tests for new CLI options: --quiet, --dry-run, --version."""

    def test_main_with_quiet_flag(self, monkeypatch):
        """Test CLI with --quiet flag suppresses output."""
        mock_save_config = mock.MagicMock()
        mock_update_firewall_rule = mock.MagicMock()
        mock_validate_firewall_id = mock.MagicMock(return_value=True)
        mock_validate_label = mock.MagicMock(return_value=True)

        monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)
        monkeypatch.setattr("acc_fwu.cli.validate_firewall_id", mock_validate_firewall_id)
        monkeypatch.setattr("acc_fwu.cli.validate_label", mock_validate_label)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '--label', 'Test-Label', '-q'])

        main()

        mock_save_config.assert_called_once_with("12345", "Test-Label", quiet=True)
        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Test-Label", debug=False, quiet=True, dry_run=False, add_ip=False
        )

    def test_main_with_dry_run_flag(self, monkeypatch):
        """Test CLI with --dry-run flag doesn't save config."""
        mock_save_config = mock.MagicMock()
        mock_update_firewall_rule = mock.MagicMock()
        mock_validate_firewall_id = mock.MagicMock(return_value=True)
        mock_validate_label = mock.MagicMock(return_value=True)

        monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)
        monkeypatch.setattr("acc_fwu.cli.validate_firewall_id", mock_validate_firewall_id)
        monkeypatch.setattr("acc_fwu.cli.validate_label", mock_validate_label)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '--label', 'Test-Label', '--dry-run'])

        main()

        # save_config should NOT be called in dry_run mode
        mock_save_config.assert_not_called()
        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Test-Label", debug=False, quiet=False, dry_run=True, add_ip=False
        )

    def test_main_with_debug_flag(self, monkeypatch):
        """Test CLI with --debug flag."""
        mock_save_config = mock.MagicMock()
        mock_update_firewall_rule = mock.MagicMock()
        mock_validate_firewall_id = mock.MagicMock(return_value=True)
        mock_validate_label = mock.MagicMock(return_value=True)

        monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)
        monkeypatch.setattr("acc_fwu.cli.validate_firewall_id", mock_validate_firewall_id)
        monkeypatch.setattr("acc_fwu.cli.validate_label", mock_validate_label)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '-d'])

        main()

        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Default-Label", debug=True, quiet=False, dry_run=False, add_ip=False
        )

    def test_main_quiet_mode_suppresses_config_error(self, monkeypatch, capsys):
        """Test that --quiet suppresses config file not found message."""
        mock_load_config = mock.MagicMock(side_effect=FileNotFoundError)

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '-q'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        # Output should be empty in quiet mode
        assert captured.out == ""


class TestCliValidation:
    """Tests for input validation in CLI."""

    def test_main_with_invalid_firewall_id(self, monkeypatch, capsys):
        """Test CLI rejects invalid firewall_id."""
        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', 'invalid-id', '--label', 'Test'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid firewall ID" in captured.err

    def test_main_with_invalid_label(self, monkeypatch, capsys):
        """Test CLI rejects invalid label."""
        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '--label', 'invalid label!'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid label" in captured.err


class TestCliErrorHandling:
    """Tests for CLI error handling."""

    def test_main_handles_api_errors(self, monkeypatch, capsys):
        """Test CLI handles API errors gracefully."""
        mock_load_config = mock.MagicMock(return_value=("12345", "Test-Label"))
        mock_update_firewall_rule = mock.MagicMock(side_effect=Exception("API error"))

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)
        monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_handles_value_error_from_firewall_functions(self, monkeypatch, capsys):
        """Test CLI handles ValueError from firewall functions."""
        mock_load_config = mock.MagicMock(return_value=("12345", "Test-Label"))
        mock_update_firewall_rule = mock.MagicMock(
            side_effect=ValueError("Some validation error")
        )

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)
        monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Validation error:" in captured.err

    def test_main_debug_mode_reraises_exceptions(self, monkeypatch):
        """Test that debug mode re-raises exceptions instead of catching them."""
        mock_load_config = mock.MagicMock(return_value=("12345", "Test-Label"))
        mock_update_firewall_rule = mock.MagicMock(
            side_effect=RuntimeError("Unexpected error")
        )

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)
        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--debug'])

        # With --debug, the exception should be re-raised, not caught
        with pytest.raises(RuntimeError, match="Unexpected error"):
            main()


class TestCliVersion:
    """Tests for version handling."""

    def test_version_is_set(self):
        """Test that __version__ is defined."""
        from acc_fwu.cli import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)

    def test_version_fallback(self, monkeypatch):
        """Test version fallback when package is not installed."""
        # This tests the fallback mechanism by importing the module
        # The version should be either the actual version or "0.0.0-dev"
        from acc_fwu.cli import __version__
        assert __version__ == "0.0.0-dev" or __version__[0].isdigit()


class TestCliAddFlag:
    """Tests for the --add flag."""

    def test_main_with_add_flag(self, monkeypatch):
        """Test CLI with --add flag passes add_ip=True."""
        mock_save_config = mock.MagicMock()
        mock_update_firewall_rule = mock.MagicMock()
        mock_validate_firewall_id = mock.MagicMock(return_value=True)
        mock_validate_label = mock.MagicMock(return_value=True)

        monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)
        monkeypatch.setattr("acc_fwu.cli.validate_firewall_id", mock_validate_firewall_id)
        monkeypatch.setattr("acc_fwu.cli.validate_label", mock_validate_label)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--firewall_id', '12345', '--label', 'Test', '-a'])

        main()

        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Test", debug=False, quiet=False, dry_run=False, add_ip=True
        )

    def test_main_add_flag_with_config(self, monkeypatch):
        """Test CLI with --add flag when using config file."""
        mock_load_config = mock.MagicMock(return_value=("12345", "Config-Label"))
        mock_update_firewall_rule = mock.MagicMock()

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--add'])

        main()

        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Config-Label", debug=False, quiet=False, dry_run=False, add_ip=True
        )


class TestCliListFlag:
    """Tests for the --list flag."""

    def test_main_with_list_flag(self, monkeypatch, capsys):
        """Test CLI with --list flag shows firewalls."""
        mock_list_firewalls = mock.MagicMock(return_value=[
            {"id": 12345, "label": "my-firewall", "status": "enabled"},
            {"id": 67890, "label": "another-fw", "status": "disabled"},
        ])

        monkeypatch.setattr("acc_fwu.cli.list_firewalls", mock_list_firewalls)
        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--list'])

        main()

        mock_list_firewalls.assert_called_once()
        captured = capsys.readouterr()
        assert "Available firewalls" in captured.out
        assert "12345" in captured.out
        assert "my-firewall" in captured.out
        assert "enabled" in captured.out

    def test_main_with_list_flag_empty(self, monkeypatch, capsys):
        """Test CLI with --list flag when no firewalls exist."""
        mock_list_firewalls = mock.MagicMock(return_value=[])

        monkeypatch.setattr("acc_fwu.cli.list_firewalls", mock_list_firewalls)
        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--list'])

        main()

        captured = capsys.readouterr()
        assert "No firewalls found" in captured.out

    def test_main_with_list_flag_error(self, monkeypatch, capsys):
        """Test CLI with --list flag handles errors."""
        mock_list_firewalls = mock.MagicMock(side_effect=Exception("API Error"))

        monkeypatch.setattr("acc_fwu.cli.list_firewalls", mock_list_firewalls)
        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--list'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error listing firewalls" in captured.err


class TestCliInteractiveSelection:
    """Tests for interactive firewall selection."""

    def test_main_interactive_selection_when_no_config(self, monkeypatch, capsys):
        """Test CLI uses interactive selection when no config file exists."""
        mock_load_config = mock.MagicMock(side_effect=FileNotFoundError)
        mock_select_firewall = mock.MagicMock(return_value="12345")
        mock_save_config = mock.MagicMock()
        mock_update_firewall_rule = mock.MagicMock()

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.select_firewall", mock_select_firewall)
        monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

        main()

        mock_select_firewall.assert_called_once()
        mock_save_config.assert_called_once()
        mock_update_firewall_rule.assert_called_once()
        captured = capsys.readouterr()
        assert "No configuration file found" in captured.out

    def test_main_interactive_selection_dry_run(self, monkeypatch, capsys):
        """Test CLI interactive selection with --dry-run doesn't save config."""
        mock_load_config = mock.MagicMock(side_effect=FileNotFoundError)
        mock_select_firewall = mock.MagicMock(return_value="12345")
        mock_save_config = mock.MagicMock()
        mock_update_firewall_rule = mock.MagicMock()

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.select_firewall", mock_select_firewall)
        monkeypatch.setattr("acc_fwu.cli.save_config", mock_save_config)
        monkeypatch.setattr("acc_fwu.cli.update_firewall_rule", mock_update_firewall_rule)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '--dry-run'])

        main()

        mock_select_firewall.assert_called_once()
        mock_save_config.assert_not_called()
        mock_update_firewall_rule.assert_called_once_with(
            "12345", "Default-Label", debug=False, quiet=False, dry_run=True, add_ip=False
        )

    def test_main_interactive_selection_cancelled(self, monkeypatch, capsys):
        """Test CLI handles cancelled interactive selection."""
        mock_load_config = mock.MagicMock(side_effect=FileNotFoundError)
        mock_select_firewall = mock.MagicMock(side_effect=ValueError("cancelled"))

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)
        monkeypatch.setattr("acc_fwu.cli.select_firewall", mock_select_firewall)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_interactive_selection_quiet_mode_errors(self, monkeypatch, capsys):
        """Test CLI in quiet mode with no config exits with error (can't do interactive selection)."""
        mock_load_config = mock.MagicMock(side_effect=FileNotFoundError)
        # Don't mock select_firewall - let it raise the real error for quiet mode

        monkeypatch.setattr("acc_fwu.cli.load_config", mock_load_config)

        monkeypatch.setattr(sys, 'argv', ['acc-fwu', '-q'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        # Should not print "No configuration file found" in quiet mode
        assert "No configuration file found" not in captured.out
        # Error message should be suppressed in quiet mode
        assert captured.out == ""
