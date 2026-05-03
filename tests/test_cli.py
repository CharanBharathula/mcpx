import pytest
from click.testing import CliRunner

from mcpx.cli import main


def test_search_command_with_query():
    runner = CliRunner()
    result = runner.invoke(main, ["search", "github"])
    assert result.exit_code == 0
    assert "github" in result.output.lower()


def test_search_command_no_query():
    runner = CliRunner()
    result = runner.invoke(main, ["search"])
    assert result.exit_code == 0
    # All 15 servers should be shown
    assert "github" in result.output.lower()
    assert "filesystem" in result.output.lower()


def test_info_command_known_server():
    runner = CliRunner()
    result = runner.invoke(main, ["info", "github"])
    assert result.exit_code == 0
    assert "github" in result.output.lower()


def test_info_command_unknown_server():
    runner = CliRunner()
    result = runner.invoke(main, ["info", "nonexistent-xyz"])
    assert result.exit_code != 0


def test_clients_command():
    runner = CliRunner()
    result = runner.invoke(main, ["clients"])
    assert result.exit_code == 0
    assert "claude" in result.output.lower()
    assert "cursor" in result.output.lower()
    assert "windsurf" in result.output.lower()


def test_install_dry_run(tmp_path, monkeypatch):
    """--dry-run should not install anything or write config files."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "memory"])
    assert result.exit_code == 0
    assert "would install" in result.output.lower()


def test_uninstall_dry_run():
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "uninstall", "memory"])
    assert result.exit_code == 0
    assert "would remove" in result.output.lower()


def test_search_returns_all_15_servers():
    runner = CliRunner()
    result = runner.invoke(main, ["search"])
    assert result.exit_code == 0
    for name in [
        "github", "filesystem", "fetch", "memory", "postgres", "sqlite",
        "brave-search", "puppeteer", "slack", "git", "time",
        "sequential-thinking", "google-maps", "gitlab", "everything",
    ]:
        assert name in result.output.lower(), f"Expected '{name}' in search output"


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_install_unknown_server():
    runner = CliRunner()
    result = runner.invoke(main, ["install", "nonexistent-xyz-server"])
    assert result.exit_code != 0


def test_update_dry_run(tmp_path, monkeypatch):
    """--dry-run update with no installed servers should report nothing to update."""
    runner = CliRunner()
    # Point claude config to empty tmp dir so no servers are installed
    from mcpx import config as cfg_module

    original = cfg_module.ConfigManager.get_client_configs

    def patched_configs(self):
        configs = original(self)
        configs["claude"]["path"] = tmp_path / "claude_config.json"
        return configs

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", patched_configs)
    result = runner.invoke(main, ["--dry-run", "update"])
    assert result.exit_code == 0
