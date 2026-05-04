import pytest
from click.testing import CliRunner

from mcp_stack.cli import main


def test_search_command_with_query():
    runner = CliRunner()
    result = runner.invoke(main, ["search", "github"])
    assert result.exit_code == 0
    assert "github" in result.output.lower()


def test_search_command_no_query():
    runner = CliRunner()
    result = runner.invoke(main, ["search"])
    assert result.exit_code == 0
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


def test_install_dry_run_memory():
    """--dry-run for a no-input server shows install and config write previews."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "memory"])
    assert result.exit_code == 0
    assert "would install" in result.output.lower()
    assert "would write config" in result.output.lower()


def test_install_dry_run_github():
    """--dry-run for github shows env-var prompt preview."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "github"])
    assert result.exit_code == 0
    assert "GITHUB_PERSONAL_ACCESS_TOKEN" in result.output
    assert "would install" in result.output.lower()


def test_install_dry_run_filesystem():
    """--dry-run for filesystem shows arg_prompt preview."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "filesystem"])
    assert result.exit_code == 0
    assert "allowed_dir" in result.output.lower()
    assert "would install" in result.output.lower()


def test_install_dry_run_postgres():
    """--dry-run for postgres shows connection_string arg_prompt preview."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "postgres"])
    assert result.exit_code == 0
    assert "connection_string" in result.output.lower()


def test_install_dry_run_sqlite():
    """--dry-run for sqlite shows db_path arg_prompt preview."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "sqlite"])
    assert result.exit_code == 0
    assert "db_path" in result.output.lower()


def test_install_dry_run_notion():
    """--dry-run for notion shows NOTION_TOKEN env prompt."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "notion"])
    assert result.exit_code == 0
    assert "NOTION_TOKEN" in result.output


def test_install_dry_run_stripe():
    """--dry-run for stripe shows STRIPE_SECRET_KEY env prompt."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "stripe"])
    assert result.exit_code == 0
    assert "STRIPE_SECRET_KEY" in result.output


def test_install_dry_run_supabase():
    """--dry-run for supabase shows access_token arg prompt."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "supabase"])
    assert result.exit_code == 0
    assert "access_token" in result.output.lower()


def test_install_dry_run_playwright():
    """--dry-run for playwright (no config needed) shows write config message."""
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "install", "playwright"])
    assert result.exit_code == 0
    assert "would write config" in result.output.lower()


def test_info_shows_notes_for_kubernetes():
    """info command shows notes for servers that need prior setup."""
    runner = CliRunner()
    result = runner.invoke(main, ["info", "kubernetes"])
    assert result.exit_code == 0
    assert "kubectl" in result.output.lower()


def test_uninstall_dry_run():
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "uninstall", "memory"])
    assert result.exit_code == 0
    assert "would remove" in result.output.lower()


def test_search_returns_all_servers():
    runner = CliRunner()
    result = runner.invoke(main, ["search"])
    assert result.exit_code == 0
    for name in [
        "github", "filesystem", "fetch", "memory", "postgres", "sqlite",
        "brave-search", "puppeteer", "slack", "git", "time",
        "sequential-thinking", "google-maps", "gitlab", "everything",
        "playwright", "sentry", "kubernetes", "docker", "notion", "azure",
        "hubspot", "figma", "supabase", "aws-kb-retrieval", "cloudflare",
        "exa", "stripe", "obsidian", "mongodb", "atlassian",
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
    from mcp_stack import config as cfg_module

    original = cfg_module.ConfigManager.get_client_configs

    def patched_configs(self):
        configs = original(self)
        configs["claude"]["path"] = tmp_path / "claude_config.json"
        return configs

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", patched_configs)
    result = runner.invoke(main, ["--dry-run", "update"])
    assert result.exit_code == 0


def test_info_shows_arg_prompts():
    """info command should show arg_prompts inputs for filesystem."""
    runner = CliRunner()
    result = runner.invoke(main, ["info", "filesystem"])
    assert result.exit_code == 0
    assert "allowed_dir" in result.output.lower()


def test_info_no_inputs_for_memory():
    """memory server has no env vars or arg_prompts."""
    runner = CliRunner()
    result = runner.invoke(main, ["info", "memory"])
    assert result.exit_code == 0
    assert "no inputs required" in result.output.lower()


def test_install_with_arg_prompt_input(tmp_path, monkeypatch):
    """install filesystem should prompt for allowed_dir and write it into args."""
    runner = CliRunner()

    from mcp_stack import config as cfg_module
    from mcp_stack import installer as ins_module

    original_cfg = cfg_module.ConfigManager.get_client_configs

    def patched_configs(self):
        configs = original_cfg(self)
        for k in configs:
            configs[k]["path"] = tmp_path / f"{k}_config.json"
        return configs

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", patched_configs)
    monkeypatch.setattr(ins_module.Installer, "check_runtime", lambda self, cmd: True)

    result = runner.invoke(
        main,
        ["install", "filesystem"],
        input="/home/user/documents\n",
    )
    assert result.exit_code == 0, result.output

    import json
    config = json.loads((tmp_path / "claude_config.json").read_text())
    args = config["mcpServers"]["filesystem"]["args"]
    assert "/home/user/documents" in args


def test_install_with_env_prompt_input(tmp_path, monkeypatch):
    """install github should prompt for token and store it in env."""
    runner = CliRunner()

    from mcp_stack import config as cfg_module
    from mcp_stack import installer as ins_module

    original_cfg = cfg_module.ConfigManager.get_client_configs

    def patched_configs(self):
        configs = original_cfg(self)
        for k in configs:
            configs[k]["path"] = tmp_path / f"{k}_config.json"
        return configs

    monkeypatch.setattr(cfg_module.ConfigManager, "get_client_configs", patched_configs)
    monkeypatch.setattr(ins_module.Installer, "check_runtime", lambda self, cmd: True)

    result = runner.invoke(
        main,
        ["install", "github"],
        input="ghp_testtoken123\n",
    )
    assert result.exit_code == 0, result.output

    import json
    config = json.loads((tmp_path / "claude_config.json").read_text())
    assert config["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "ghp_testtoken123"
