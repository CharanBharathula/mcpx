import json
from pathlib import Path

import pytest

from mcp_stack.config import ConfigManager


def test_get_client_configs_keys():
    cm = ConfigManager()
    configs = cm.get_client_configs()
    assert "claude" in configs
    assert "cursor" in configs
    assert "windsurf" in configs


def test_get_client_configs_has_paths():
    cm = ConfigManager()
    configs = cm.get_client_configs()
    for client_id, client_info in configs.items():
        assert "path" in client_info
        assert "name" in client_info
        assert isinstance(client_info["path"], Path)


def test_read_config_missing_file(tmp_path):
    cm = ConfigManager()
    config_path = tmp_path / "nonexistent.json"
    config = cm.read_config(config_path)
    assert "mcpServers" in config
    assert config["mcpServers"] == {}


def test_read_config_existing(tmp_path):
    cm = ConfigManager()
    config_path = tmp_path / "config.json"
    data = {"mcpServers": {"test-server": {"command": "npx", "args": ["-y", "test"]}}}
    config_path.write_text(json.dumps(data))
    config = cm.read_config(config_path)
    assert "test-server" in config["mcpServers"]


def test_write_config_creates_file(tmp_path):
    cm = ConfigManager()
    config_path = tmp_path / "subdir" / "config.json"
    config = {"mcpServers": {"my-server": {"command": "npx", "args": []}}}
    cm.write_config(config_path, config)
    assert config_path.exists()
    loaded = json.loads(config_path.read_text())
    assert "my-server" in loaded["mcpServers"]


def test_add_server_to_config(tmp_path):
    cm = ConfigManager()
    config_path = tmp_path / "config.json"
    server_config = {"command": "npx", "args": ["-y", "@test/server"], "env": {"KEY": "val"}}
    cm.add_server(config_path, "test-server", server_config)
    config = cm.read_config(config_path)
    assert "test-server" in config["mcpServers"]
    assert config["mcpServers"]["test-server"]["command"] == "npx"


def test_add_server_updates_existing(tmp_path):
    cm = ConfigManager()
    config_path = tmp_path / "config.json"
    cm.add_server(config_path, "my-server", {"command": "npx", "args": ["-y", "pkg-v1"]})
    cm.add_server(config_path, "my-server", {"command": "npx", "args": ["-y", "pkg-v2"]})
    config = cm.read_config(config_path)
    assert config["mcpServers"]["my-server"]["args"] == ["-y", "pkg-v2"]


def test_remove_server_from_config(tmp_path):
    cm = ConfigManager()
    config_path = tmp_path / "config.json"
    cm.add_server(config_path, "to-remove", {"command": "npx", "args": []})
    result = cm.remove_server(config_path, "to-remove")
    assert result is True
    config = cm.read_config(config_path)
    assert "to-remove" not in config["mcpServers"]


def test_get_installed_servers(tmp_path):
    cm = ConfigManager()
    config_path = tmp_path / "config.json"
    cm.add_server(config_path, "server-a", {"command": "npx", "args": []})
    cm.add_server(config_path, "server-b", {"command": "npx", "args": []})
    installed = cm.get_installed_servers(config_path)
    assert "server-a" in installed
    assert "server-b" in installed
