import pytest

from mcpx.installer import Installer


def test_build_server_config_basic():
    installer = Installer()
    server = {"command": "npx", "args": ["-y", "@test/server"], "env": []}
    config = installer.build_server_config(server)
    assert config["command"] == "npx"
    assert config["args"] == ["-y", "@test/server"]


def test_build_server_config_with_env():
    installer = Installer()
    server = {
        "command": "npx",
        "args": ["-y", "@test/server"],
        "env": [{"name": "API_KEY", "description": "API key", "required": True}],
    }
    env_values = {"API_KEY": "test-key-123"}
    config = installer.build_server_config(server, env_values)
    assert "env" in config
    assert config["env"]["API_KEY"] == "test-key-123"


def test_build_server_config_args_copy():
    installer = Installer()
    original_args = ["-y", "@test/server"]
    server = {"command": "npx", "args": original_args, "env": []}
    config = installer.build_server_config(server)
    config["args"].append("--extra")
    # Mutation of returned args must not affect the input list
    assert original_args == ["-y", "@test/server"]
