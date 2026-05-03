# mcpx

A package manager for MCP servers. Install, configure, and manage [Model Context Protocol](https://modelcontextprotocol.io/) servers across **Claude Desktop**, **Cursor**, and **Windsurf** with a single command — no manual JSON editing.

```
mcpx install github
```

That one command installs the GitHub MCP server, prompts for your token, and writes the config into all three clients automatically.

---

## Install

**Requirements:** Python 3.9+, Node.js 18+ (for npx-based servers)

```bash
pip install mcpx
```

Or from source:

```bash
git clone https://github.com/CharanBharathula/mcpx.git
cd mcpx
pip install -e ".[dev]"
```

---

## Commands

| Command | Description |
|---------|-------------|
| `mcpx install <server>` | Install and configure an MCP server |
| `mcpx uninstall <server>` | Remove an MCP server from all client configs |
| `mcpx search [query]` | Search the server registry |
| `mcpx info <server>` | Show details and required inputs for a server |
| `mcpx list` | List installed servers for a client |
| `mcpx clients` | Show supported clients and their config paths |
| `mcpx run <server>` | Run a server directly for testing |
| `mcpx update [server]` | Update server(s) to the latest version |

All commands support `--dry-run` to preview changes without applying them.

### Options

```
mcpx install github --client claude          # install for one client only
mcpx install github --client cursor --client windsurf
mcpx --dry-run install filesystem            # preview without writing
mcpx list --client cursor                    # list servers for Cursor
```

---

## Registry — 31 servers

### No configuration required

| Server | Description |
|--------|-------------|
| `memory` | Knowledge graph persistent memory |
| `fetch` | Web content fetching and conversion |
| `puppeteer` | Browser automation (Puppeteer) |
| `playwright` | Browser automation (Playwright) |
| `sequential-thinking` | Structured problem-solving |
| `everything` | Reference/test server |
| `docker` | Docker container management* |
| `kubernetes` | Kubernetes cluster management* |
| `azure` | Azure cloud management* |
| `cloudflare` | Cloudflare Workers, KV, D1, R2* |
| `git` | Git operations (requires uv) |
| `time` | Time/timezone utilities (requires uv) |

*Requires prior auth setup — run `mcpx info <server>` for details.

### Requires API key / token

| Server | What you need |
|--------|---------------|
| `github` | GitHub Personal Access Token |
| `gitlab` | GitLab Personal Access Token |
| `brave-search` | Brave Search API key |
| `google-maps` | Google Maps API key |
| `slack` | Slack Bot Token |
| `notion` | Notion Integration Token |
| `hubspot` | HubSpot Private App Token |
| `figma` | Figma Personal Access Token |
| `exa` | Exa AI API key |
| `stripe` | Stripe Secret Key |
| `aws-kb-retrieval` | AWS credentials + region |
| `atlassian` | Atlassian API token (Jira + Confluence) |
| `mongodb` | MongoDB connection string |

### Requires path input at install time

| Server | What you need |
|--------|---------------|
| `filesystem` | Directory path to allow access |
| `sqlite` | Path to SQLite database file |
| `postgres` | PostgreSQL connection string |
| `supabase` | Supabase personal access token |
| `sentry` | Sentry auth token |
| `obsidian` | Path to Obsidian vault |

---

## How it works

1. `mcpx install memory` — verifies Node.js is available
2. Prompts for any required API keys or paths
3. Writes the server config into:
   - **Claude Desktop**: `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
   - **Cursor**: `~/.cursor/mcp.json`
   - **Windsurf**: `~/.codeium/windsurf/mcp_config.json`
4. Restart your client — the server is ready

Packages are **not** installed globally. `npx -y` downloads them on first use.

---

## Development

```bash
pip install -e ".[dev]"
pytest -v        # 65 tests
```

### Project structure

```
mcpx/
  cli.py          # Click commands
  installer.py    # Runtime check + config builder
  registry.py     # Registry loader + search
  config.py       # Client config read/write
  registry.json   # 31 bundled server definitions
tests/
  test_cli.py
  test_config.py
  test_installer.py
  test_registry.py
pyproject.toml
```

---

## Contributing

Pull requests welcome. To add a new server, add an entry to `mcpx/registry.json` following the existing schema and add tests in `tests/test_registry.py`.

---

## License

MIT — see [LICENSE](LICENSE)
