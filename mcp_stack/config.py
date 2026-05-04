import json
import os
import platform
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MCP_STACK_DIR = Path.home() / ".mcp-stack"


class ConfigManager:
    def get_client_configs(self) -> Dict[str, dict]:
        home = Path.home()
        system = platform.system()

        if system == "Darwin":
            claude_path = (
                home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
            )
        elif system == "Windows":
            appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
            claude_path = appdata / "Claude" / "claude_desktop_config.json"
        else:
            claude_path = home / ".config" / "Claude" / "claude_desktop_config.json"

        return {
            "claude": {
                "name": "Claude Desktop",
                "path": claude_path,
            },
            "cursor": {
                "name": "Cursor",
                "path": home / ".cursor" / "mcp.json",
            },
            "windsurf": {
                "name": "Windsurf",
                "path": home / ".codeium" / "windsurf" / "mcp_config.json",
            },
        }

    def read_config(self, config_path: Path) -> dict:
        if not config_path.exists():
            return {"mcpServers": {}}
        with open(config_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        if "mcpServers" not in data:
            data["mcpServers"] = {}
        return data

    def write_config(self, config_path: Path, config: dict) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def add_server(self, config_path: Path, server_name: str, server_config: dict) -> None:
        config = self.read_config(config_path)
        config["mcpServers"][server_name] = server_config
        self.write_config(config_path, config)

    def remove_server(self, config_path: Path, server_name: str) -> bool:
        config = self.read_config(config_path)
        if server_name in config.get("mcpServers", {}):
            del config["mcpServers"][server_name]
            self.write_config(config_path, config)
            return True
        return False

    def get_installed_servers(self, config_path: Path) -> dict:
        config = self.read_config(config_path)
        return config.get("mcpServers", {})

    # ------------------------------------------------------------------
    # Backup / Restore
    # ------------------------------------------------------------------

    def backup(self) -> Tuple[Path, List[str]]:
        """Copy all existing client configs to ~/.mcp-stack/backups/<timestamp>/."""
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir = MCP_STACK_DIR / "backups" / ts
        backup_dir.mkdir(parents=True, exist_ok=True)

        backed_up: List[str] = []
        for client_id, client_info in self.get_client_configs().items():
            path = client_info["path"]
            if path.exists():
                shutil.copy2(path, backup_dir / f"{client_id}.json")
                backed_up.append(client_id)

        return backup_dir, backed_up

    def list_backups(self) -> List[Path]:
        """Return backup directories sorted newest-first."""
        backups_dir = MCP_STACK_DIR / "backups"
        if not backups_dir.exists():
            return []
        return sorted(
            [p for p in backups_dir.iterdir() if p.is_dir()],
            reverse=True,
        )

    def restore(self, backup_dir: Path) -> List[str]:
        """Copy configs from backup_dir back to each client's config path."""
        restored: List[str] = []
        for client_id, client_info in self.get_client_configs().items():
            backup_file = backup_dir / f"{client_id}.json"
            if backup_file.exists():
                config_path = client_info["path"]
                config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, config_path)
                restored.append(client_id)
        return restored
