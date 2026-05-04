import shutil
from typing import Dict, Optional


class Installer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def check_runtime(self, command: str) -> bool:
        """Return True if the runtime command (npx, uvx, etc.) is on PATH."""
        return shutil.which(command) is not None

    def install_package(self, package: str, command: str = "npx") -> bool:
        """Verify the required runtime is available.

        MCP servers don't need a global pre-install — npx -y and uvx download
        the package automatically on first use.
        """
        if self.dry_run:
            return True
        return self.check_runtime(command)

    def build_server_config(
        self,
        server_def: dict,
        env_values: Optional[Dict[str, str]] = None,
        arg_values: Optional[Dict[str, str]] = None,
    ) -> dict:
        """Build the MCP server config dict, substituting any {placeholder} args."""
        args = [
            (arg_values or {}).get(arg[1:-1], arg)
            if (arg.startswith("{") and arg.endswith("}"))
            else arg
            for arg in server_def["args"]
        ]
        config: dict = {"command": server_def["command"], "args": args}
        if env_values:
            config["env"] = dict(env_values)
        return config
