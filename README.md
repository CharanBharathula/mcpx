# mcp-ctl — The Universal Package Manager for MCP Servers 🚀

[![PyPI version](https://img.shields.io/pypi/v/mcp-ctl.svg)](https://pypi.org/project/mcp-ctl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/CharanBharathula/mcpx/actions/workflows/ci.yml/badge.svg)](https://github.com/CharanBharathula/mcpx/actions)

Stop editing `mcp_config.json` by hand. **mcp-ctl** is a unified CLI to install, configure, and manage [Model Context Protocol](https://modelcontextprotocol.io/) servers across all major AI IDEs and desktops.

```bash
mcp-ctl install github
```

One command installs the server, prompts for required environment variables (like API tokens), and automatically syncs the configuration to **Claude Desktop**, **Cursor**, and **Windsurf**.

---

## ✨ Key Features

- 🔄 **Multi-Client Sync**: Update configuration for all your AI tools at once.
- 📦 **Built-in Registry**: Direct access to 30+ production-ready MCP servers.
- 🛠️ **Zero Global Bloat**: Servers run via `npx` or virtual environments on-demand.
- 🛡️ **Validated Configs**: No more syntax errors or broken paths in your JSON files.
- 🔍 **Discovery**: Search and inspect server requirements before installing.

---

## 📦 Supported Clients

| Client | Windows Path | macOS Path |
| :--- | :--- | :--- |
| **Claude Desktop** | `%APPDATA%\Claude\...` | `~/Library/Application Support/...` |
| **Cursor** | `~/.cursor/mcp.json` | `~/.cursor/mcp.json` |
| **Windsurf** | `~/.codeium/windsurf/...` | `~/.codeium/windsurf/...` |

---

## 🛠️ Installation

**Requirements:** Python 3.9+, Node.js 18+ (for npx-based servers).

```bash
pip install mcp-ctl
```

### From Source
```bash
git clone https://github.com/CharanBharathula/mcpx.git
cd mcpx
pip install -e ".[dev]"
```

---

## 📃 Command Reference

| Command | Action |
| :--- | :--- |
| `mcp-ctl install <server>` | Interactive installation & config injection |
| `mcp-ctl uninstall <server>` | Clean removal from all client configs |
| `mcp-ctl search <query>` | Search the community registry |
| `mcp-ctl list` | View all installed servers per client |
| `mcp-ctl run <server>` | Execute a server directly for testing |
| `mcp-ctl info <server>` | View required API keys and inputs |
| `mcp-ctl update` | Batch update all servers to latest versions |

> **Pro Tip:** Use `--dry-run` with any command to see what changes would be made without writing to disk.

---

## 📑 Integrated Registry (30+ Servers)

**mcp-ctl** comes pre-loaded with optimized configurations for:

### 🔗 Standard (No Config)
- `memory`: Knowledge graph persistent memory
- `fetch`: Web content retrieval & markdown conversion
- `playwright` / `puppeteer`: Full browser automation
- `docker` / `kubernetes`: Infrastructure management
- `sequential-thinking`: Structured reasoning

### 🔑 API-Powered (Requires Key)
- `github` / `gitlab`: Repository & PR management
- `brave-search` / `exa`: Real-time web search
- `notion` / `slack` / `hubspot`: Workplace productivity
- `stripe`: Financial operations
- `sentry`: Error tracking & observability

### 📁 File-System & DB
- `filesystem`: Controlled directory access
- `sqlite` / `postgres` / `mongodb`: Native database queries

---

## 🤝 Contributing

We love new servers! To add a server to the registry:
1. Fork the repo.
2. Add your server definition to `mcpx/registry.json`.
3. Add a test case in `tests/test_registry.py`.
4. Submit a Pull Request.

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.
