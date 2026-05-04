import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

MCP_CTL_DIR = Path.home() / ".mcp-ctl"
CUSTOM_REGISTRY_PATH = MCP_CTL_DIR / "registry.json"
REGISTRY_UPDATE_URL = (
    "https://raw.githubusercontent.com/CharanBharathula/mcpx/main/mcp_ctl/registry.json"
)


class Registry:
    def __init__(self):
        registry_path = Path(__file__).parent / "registry.json"
        with open(registry_path) as f:
            data = json.load(f)
        self._servers: Dict[str, dict] = {s["name"]: s for s in data["servers"]}

        # Merge custom registry if present (custom entries override bundled ones)
        if CUSTOM_REGISTRY_PATH.exists():
            try:
                with open(CUSTOM_REGISTRY_PATH) as f:
                    custom_data = json.load(f)
                for s in custom_data.get("servers", []):
                    self._servers[s["name"]] = s
            except (json.JSONDecodeError, KeyError):
                pass

    def get_server(self, name: str) -> Optional[dict]:
        return self._servers.get(name)

    def search(self, query: str = "") -> List[dict]:
        if not query:
            return list(self._servers.values())
        q = query.lower()
        results = []
        for server in self._servers.values():
            if (
                q in server["name"].lower()
                or q in server["description"].lower()
                or any(q in tag.lower() for tag in server.get("tags", []))
            ):
                results.append(server)
        return results

    def list_names(self) -> List[str]:
        return list(self._servers.keys())

    def all_servers(self) -> List[dict]:
        return list(self._servers.values())

    def fetch_remote(self, url: str) -> List[dict]:
        """Fetch and return servers list from a remote registry URL."""
        req = urllib.request.Request(url, headers={"User-Agent": "mcp-ctl/0.1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("servers", [])

    def save_custom(self, new_servers: List[dict]) -> int:
        """Merge new_servers into ~/.mcp-ctl/registry.json. Returns count added/updated."""
        MCP_CTL_DIR.mkdir(parents=True, exist_ok=True)
        existing: Dict[str, dict] = {}
        if CUSTOM_REGISTRY_PATH.exists():
            try:
                with open(CUSTOM_REGISTRY_PATH) as f:
                    for s in json.load(f).get("servers", []):
                        existing[s["name"]] = s
            except (json.JSONDecodeError, KeyError):
                pass

        for s in new_servers:
            existing[s["name"]] = s

        with open(CUSTOM_REGISTRY_PATH, "w") as f:
            json.dump({"version": "1.0.0", "servers": list(existing.values())}, f, indent=2)

        return len(new_servers)
