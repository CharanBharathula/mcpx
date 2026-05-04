"""Tests for the 6 new features: doctor, profile, backup, restore, registry, export."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mcpx.cli import main
from mcpx.config import ConfigManager
from mcpx.registry import Registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patched_configs(tmp_path):
    """Return a monkeypatch helper that redirects all client config paths to tmp_path."""
    from mcpx import config as cfg_module

    original = cfg_module.ConfigManager.get_client_configs

    def patched(self):
        configs = original(self)
        for k in configs:
            configs[k]["path"] = tmp_path / f"{k}.json"
        return configs

    return patched


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


def test_doctor_runs_without_error():
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "Node.js" in result.output or "npx" in result.output


def test_doctor_shows_client_config_status():
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "Claude Desktop" in result.output
    assert "Cursor" in result.output
    assert "Windsurf" in result.output


def test_doctor_shows_installed_servers(tmp_path, monkeypatch):
    from mcpx import config as cfg_module

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", _patched_configs(tmp_path))

    cm = ConfigManager()
    configs = cm.get_client_configs()
    cm.add_server(configs["claude"]["path"], "memory", {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"]})

    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "memory" in result.output


def test_doctor_flags_unknown_runtime(tmp_path, monkeypatch):
    from mcpx import config as cfg_module

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", _patched_configs(tmp_path))

    cm = ConfigManager()
    configs = cm.get_client_configs()
    cm.add_server(configs["claude"]["path"], "badserver", {"command": "no-such-runtime-xyz", "args": []})

    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "fail" in result.output.lower() or "not in PATH" in result.output


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------


def test_profile_list():
    runner = CliRunner()
    result = runner.invoke(main, ["profile", "list"])
    assert result.exit_code == 0
    for name in ("dev", "data", "ai", "devops", "writing", "payments", "search", "fullstack"):
        assert name in result.output


def test_profile_show_known():
    runner = CliRunner()
    result = runner.invoke(main, ["profile", "show", "dev"])
    assert result.exit_code == 0
    assert "github" in result.output
    assert "docker" in result.output


def test_profile_show_unknown():
    runner = CliRunner()
    result = runner.invoke(main, ["profile", "show", "nonexistent-profile-xyz"])
    assert result.exit_code != 0


def test_profile_install_dry_run():
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "profile", "install", "ai"])
    assert result.exit_code == 0
    assert "memory" in result.output.lower()
    assert "fetch" in result.output.lower()


def test_profile_install_no_config_servers(tmp_path, monkeypatch):
    """Install the devops profile — all servers need no API keys."""
    from mcpx import config as cfg_module
    from mcpx import installer as ins_module

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", _patched_configs(tmp_path))
    monkeypatch.setattr(ins_module.Installer, "check_runtime", lambda self, cmd: True)

    runner = CliRunner()
    result = runner.invoke(main, ["profile", "install", "devops"])
    assert result.exit_code == 0
    assert "devops" in result.output.lower()

    config = json.loads((tmp_path / "claude.json").read_text())
    assert "docker" in config["mcpServers"]
    assert "kubernetes" in config["mcpServers"]


# ---------------------------------------------------------------------------
# backup
# ---------------------------------------------------------------------------


def test_backup_creates_files(tmp_path, monkeypatch):
    from mcpx import config as cfg_module
    from mcpx.config import MCPX_DIR

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", _patched_configs(tmp_path))
    monkeypatch.setattr("mcpx.config.MCPX_DIR", tmp_path / ".mcpx")

    cm = ConfigManager()
    configs = cm.get_client_configs()
    cm.add_server(configs["claude"]["path"], "memory", {"command": "npx", "args": []})

    runner = CliRunner()
    result = runner.invoke(main, ["backup"])
    assert result.exit_code == 0
    assert "claude" in result.output


def test_backup_list_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("mcpx.config.MCPX_DIR", tmp_path / ".mcpx")

    runner = CliRunner()
    result = runner.invoke(main, ["backup", "--list"])
    assert result.exit_code == 0
    assert "no backups" in result.output.lower()


def test_backup_and_restore_roundtrip(tmp_path, monkeypatch):
    from mcpx import config as cfg_module

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", _patched_configs(tmp_path))
    monkeypatch.setattr("mcpx.config.MCPX_DIR", tmp_path / ".mcpx")

    cm = ConfigManager()
    configs = cm.get_client_configs()
    claude_path = configs["claude"]["path"]

    cm.add_server(claude_path, "memory", {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"]})

    backup_dir, backed_up = cm.backup()
    assert "claude" in backed_up
    assert (backup_dir / "claude.json").exists()

    cm.remove_server(claude_path, "memory")
    assert cm.get_installed_servers(claude_path) == {}

    restored = cm.restore(backup_dir)
    assert "claude" in restored
    assert "memory" in cm.get_installed_servers(claude_path)


def test_restore_no_backups(tmp_path, monkeypatch):
    monkeypatch.setattr("mcpx.config.MCPX_DIR", tmp_path / ".mcpx")

    runner = CliRunner()
    result = runner.invoke(main, ["restore"])
    assert result.exit_code == 0
    assert "no backups" in result.output.lower()


# ---------------------------------------------------------------------------
# registry update / add
# ---------------------------------------------------------------------------


def test_registry_update_mocked(tmp_path, monkeypatch):
    monkeypatch.setattr("mcpx.registry.MCPX_DIR", tmp_path / ".mcpx")
    monkeypatch.setattr("mcpx.registry.CUSTOM_REGISTRY_PATH", tmp_path / ".mcpx" / "registry.json")

    fake_servers = [
        {
            "name": "test-server-xyz",
            "description": "A test server",
            "package": "@test/server-xyz",
            "command": "npx",
            "args": ["-y", "@test/server-xyz"],
            "env": [],
            "arg_prompts": [],
            "tags": ["test"],
        }
    ]

    def fake_fetch(self, url):
        return fake_servers

    from mcpx import registry as reg_module
    monkeypatch.setattr(reg_module.Registry, "fetch_remote", fake_fetch)

    runner = CliRunner()
    result = runner.invoke(main, ["registry", "update"])
    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_registry_add_mocked(tmp_path, monkeypatch):
    monkeypatch.setattr("mcpx.registry.MCPX_DIR", tmp_path / ".mcpx")
    monkeypatch.setattr("mcpx.registry.CUSTOM_REGISTRY_PATH", tmp_path / ".mcpx" / "registry.json")

    fake_servers = [
        {
            "name": "custom-server-abc",
            "description": "Custom server",
            "package": "@custom/server-abc",
            "command": "npx",
            "args": ["-y", "@custom/server-abc"],
            "env": [],
            "arg_prompts": [],
            "tags": ["custom"],
        }
    ]

    from mcpx import registry as reg_module
    monkeypatch.setattr(reg_module.Registry, "fetch_remote", lambda self, url: fake_servers)

    runner = CliRunner()
    result = runner.invoke(main, ["registry", "add", "https://example.com/registry.json"])
    assert result.exit_code == 0
    assert "custom-server-abc" in result.output


def test_registry_save_and_load_custom(tmp_path, monkeypatch):
    monkeypatch.setattr("mcpx.registry.MCPX_DIR", tmp_path / ".mcpx")
    monkeypatch.setattr("mcpx.registry.CUSTOM_REGISTRY_PATH", tmp_path / ".mcpx" / "registry.json")

    r = Registry()
    assert r.get_server("my-custom-srv") is None

    r.save_custom([{
        "name": "my-custom-srv",
        "description": "Custom",
        "package": "@my/custom-srv",
        "command": "npx",
        "args": ["-y", "@my/custom-srv"],
        "env": [],
        "arg_prompts": [],
        "tags": [],
    }])

    r2 = Registry()
    assert r2.get_server("my-custom-srv") is not None
    assert r2.get_server("my-custom-srv")["package"] == "@my/custom-srv"


def test_registry_add_empty_url(tmp_path, monkeypatch):
    from mcpx import registry as reg_module
    monkeypatch.setattr(reg_module.Registry, "fetch_remote", lambda self, url: [])

    runner = CliRunner()
    result = runner.invoke(main, ["registry", "add", "https://example.com/empty.json"])
    assert result.exit_code == 0
    assert "no servers" in result.output.lower()


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


def test_export_stdout(tmp_path, monkeypatch):
    from mcpx import config as cfg_module

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", _patched_configs(tmp_path))

    cm = ConfigManager()
    configs = cm.get_client_configs()
    cm.add_server(
        configs["claude"]["path"],
        "memory",
        {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"]},
    )

    runner = CliRunner()
    result = runner.invoke(main, ["export", "--client", "claude"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["mcpx_export"] == "1.0.0"
    assert "memory" in data["servers"]
    assert data["source_client"] == "claude"


def test_export_to_file(tmp_path, monkeypatch):
    from mcpx import config as cfg_module

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", _patched_configs(tmp_path))

    cm = ConfigManager()
    configs = cm.get_client_configs()
    cm.add_server(
        configs["claude"]["path"],
        "memory",
        {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"]},
    )

    out_file = tmp_path / "export.json"
    runner = CliRunner()
    result = runner.invoke(main, ["export", "--client", "claude", "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()

    data = json.loads(out_file.read_text())
    assert "memory" in data["servers"]


def test_export_empty_client(tmp_path, monkeypatch):
    from mcpx import config as cfg_module

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", _patched_configs(tmp_path))

    runner = CliRunner()
    result = runner.invoke(main, ["export", "--client", "claude"])
    assert result.exit_code == 0
    assert "no servers" in result.output.lower()
