import pytest

from mcpx.installer import Installer


def test_build_server_config_basic():
    installer = Installer()
    server = {"command": "npx", "args": ["-y", "@test/server"]}
    config = installer.build_server_config(server)
    assert config["command"] == "npx"
    assert config["args"] == ["-y", "@test/server"]


def test_build_server_config_with_env():
    installer = Installer()
    server = {
        "command": "npx",
        "args": ["-y", "@test/server"],
    }
    env_values = {"API_KEY": "test-key-123"}
    config = installer.build_server_config(server, env_values=env_values)
    assert "env" in config
    assert config["env"]["API_KEY"] == "test-key-123"


def test_build_server_config_args_copy():
    installer = Installer()
    original_args = ["-y", "@test/server"]
    server = {"command": "npx", "args": original_args}
    config = installer.build_server_config(server)
    config["args"].append("--extra")
    assert original_args == ["-y", "@test/server"]


def test_build_server_config_arg_substitution():
    installer = Installer()
    server = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "{allowed_dir}"],
    }
    config = installer.build_server_config(server, arg_values={"allowed_dir": "/home/user/docs"})
    assert config["args"] == ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/docs"]


def test_build_server_config_multiple_arg_substitutions():
    installer = Installer()
    server = {
        "command": "npx",
        "args": ["-y", "@test/server", "--host", "{host}", "--port", "{port}"],
    }
    config = installer.build_server_config(
        server, arg_values={"host": "localhost", "port": "5432"}
    )
    assert config["args"] == ["-y", "@test/server", "--host", "localhost", "--port", "5432"]


def test_build_server_config_no_substitution_without_arg_values():
    installer = Installer()
    server = {
        "command": "npx",
        "args": ["-y", "@test/server", "{placeholder}"],
    }
    config = installer.build_server_config(server)
    assert config["args"] == ["-y", "@test/server", "{placeholder}"]


def test_check_runtime_known_command():
    installer = Installer()
    # 'python' or 'python3' is always available in the test environment
    assert installer.check_runtime("python") or installer.check_runtime("python3")


def test_check_runtime_missing_command():
    installer = Installer()
    assert installer.check_runtime("definitely-not-a-real-command-xyz-abc") is False


def test_install_package_dry_run_always_true():
    installer = Installer(dry_run=True)
    assert installer.install_package("any-package", "definitely-not-a-runtime-xyz") is True


def test_install_package_checks_runtime():
    installer = Installer()
    assert installer.install_package("any-package", "definitely-not-a-runtime-xyz") is False
