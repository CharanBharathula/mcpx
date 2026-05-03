import json
from pathlib import Path
from typing import Dict, List, Optional


class Registry:
    def __init__(self):
        registry_path = Path(__file__).parent / "registry.json"
        with open(registry_path) as f:
            data = json.load(f)
        self._servers: Dict[str, dict] = {s["name"]: s for s in data["servers"]}

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
