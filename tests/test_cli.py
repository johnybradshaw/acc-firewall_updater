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
            "12345", "Test-Label", debug=False, quiet=False, dry_run=False
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
            "12345", "Loaded-Label", debug=False, quiet=False, dry_run=False
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
            "12345", "Test-Label", debug=False, quiet=True, dry_run=False
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
            "12345", "Test-Label", debug=False, quiet=False, dry_run=True
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
            "12345", "Default-Label", debug=True, quiet=False, dry_run=False
        )


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
