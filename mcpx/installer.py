import subprocess
from typing import Dict, Optional


class Installer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def install_package(self, package: str) -> bool:
        if self.dry_run:
            return True
        result = subprocess.run(
            ["npm", "install", "-g", package],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def build_server_config(
        self, server_def: dict, env_values: Optional[Dict[str, str]] = None
    ) -> dict:
        config: dict = {
            "command": server_def["command"],
            "args": list(server_def["args"]),
        }
        if env_values:
            config["env"] = dict(env_values)
        return config
