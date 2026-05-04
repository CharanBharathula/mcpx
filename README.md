# mcp-nest — The Universal Package Manager for MCP Servers 🚀

[![PyPI version](https://img.shields.io/pypi/v/mcp-nest.svg)](https://pypi.org/project/mcp-nest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/CharanBharathula/mcpx/actions/workflows/ci.yml/badge.svg)](https://github.com/CharanBharathula/mcpx/actions)

Stop editing `mcp_config.json` by hand. **mcp-nest** is a unified CLI to install, configure, and manage [Model Context Protocol](https://modelcontextprotocol.io/) servers across all major AI IDEs and desktops — with a single command.

```bash
pip install mcp-nest
mcp-nest install github
```

One command installs the server, prompts for required API tokens, and automatically writes the configuration to **Claude Desktop**, **Cursor**, and **Windsurf**.

---

## ✨ Key Features

- 🔄 **Multi-Client Sync** — Configure all your AI tools at once
- 📦 **Built-in Registry** — 31 production-ready MCP servers out of the box
- 🛠️ **Zero Global Bloat** — Servers run via `npx`/`uvx` on-demand, nothing installed globally
- 🛡️ **Validated Configs** — No more syntax errors or broken JSON files
- 🔍 **Discovery** — Search and inspect server requirements before installing
- 🩺 **Doctor** — Health check for runtimes, client configs, and installed servers
- 🗂️ **Profiles** — Install curated server bundles in one command
- 💾 **Backup & Restore** — Snapshot and recover all client configs
- 📤 **Export** — Share your server setup as a portable JSON file

---

## 📦 Supported Clients

| Client | Windows | macOS / Linux |
| :--- | :--- | :--- |
| **Claude Desktop** | `%APPDATA%\Claude\claude_desktop_config.json` | `~/Library/Application Support/Claude/...` |
| **Cursor** | `~/.cursor/mcp.json` | `~/.cursor/mcp.json` |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | `~/.codeium/windsurf/mcp_config.json` |

---

## 🛠️ Installation

**Requirements:** Python 3.9+, Node.js 18+ (for npx-based servers).

```bash
pip install mcp-nest
```

### From Source
```bash
git clone https://github.com/CharanBharathula/mcpx.git
cd mcpx
pip install -e ".[dev]"
```

---

## 📃 Command Reference

### Core

| Command | Description |
| :--- | :--- |
| `mcp-nest install <server>` | Install a server and write config to all clients |
| `mcp-nest uninstall <server>` | Remove a server from all client configs |
| `mcp-nest list` | List installed servers for a client |
| `mcp-nest search [query]` | Search the registry |
| `mcp-nest info <server>` | Show required inputs and details |
| `mcp-nest update [server]` | Update installed server(s) |
| `mcp-nest run <server>` | Run a server directly for testing |
| `mcp-nest clients` | Show supported clients and their config paths |

### Profiles

| Command | Description |
| :--- | :--- |
| `mcp-nest profile list` | List all built-in profiles |
| `mcp-nest profile show <name>` | Show servers in a profile |
| `mcp-nest profile install <name>` | Install all servers in a profile |

### Backup & Restore

| Command | Description |
| :--- | :--- |
| `mcp-nest backup` | Backup all client configs to `~/.mcp-nest/backups/` |
| `mcp-nest backup --list` | List available backups |
| `mcp-nest restore [timestamp]` | Restore configs from a backup |

### Registry

| Command | Description |
| :--- | :--- |
| `mcp-nest registry update` | Pull latest server list from GitHub |
| `mcp-nest registry add <url>` | Add servers from a custom registry URL |

### Export

| Command | Description |
| :--- | :--- |
| `mcp-nest export --client claude` | Export installed servers as JSON |
| `mcp-nest export -o servers.json` | Save export to a file |

> **Pro Tip:** Add `--dry-run` to any command to preview changes without writing to disk.

---

## 🗂️ Built-in Profiles

Install a full suite of servers in one command:

```bash
mcp-nest profile install dev
```

| Profile | Servers |
| :--- | :--- |
| `dev` | github, git, filesystem, docker, playwright |
| `data` | postgres, sqlite, mongodb, memory |
| `ai` | memory, sequential-thinking, fetch, exa, brave-search |
| `devops` | docker, kubernetes, cloudflare, azure |
| `writing` | notion, obsidian, memory, fetch |
| `payments` | stripe, hubspot |
| `search` | brave-search, exa, fetch, google-maps |
| `fullstack` | github, supabase, postgres, playwright, figma |

---

## 📑 Integrated Registry (31 Servers)

### 🔗 Standard (No Config Required)
`memory` · `fetch` · `playwright` · `puppeteer` · `docker` · `kubernetes` · `sequential-thinking` · `git` · `time`

### 🔑 API-Powered
`github` · `gitlab` · `brave-search` · `exa` · `notion` · `slack` · `hubspot` · `stripe` · `sentry` · `atlassian` · `figma` · `google-maps` · `azure` · `cloudflare` · `aws-kb-retrieval`

### 📁 File-System & Database
`filesystem` · `sqlite` · `postgres` · `mongodb` · `obsidian` · `supabase`

---

## 🤝 Contributing

We love new servers! To add one to the registry:
1. Fork the repo.
2. Add your server definition to `mcp_nest/registry.json`.
3. Add a test in `tests/test_registry.py`.
4. Submit a Pull Request.

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.
