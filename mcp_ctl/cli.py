import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import ConfigManager
from .installer import Installer
from .registry import REGISTRY_UPDATE_URL, Registry

_RUNTIME_INSTALL_HINTS = {
    "npx": "Node.js not found. Install from https://nodejs.org",
    "node": "Node.js not found. Install from https://nodejs.org",
    "uvx": "uv not found. Install from https://docs.astral.sh/uv/",
}


def _console() -> Console:
    """Return a Console writing to current sys.stdout (CliRunner-compatible)."""
    return Console(highlight=False)


def _load_profiles() -> dict:
    profiles_path = Path(__file__).parent / "profiles.json"
    with open(profiles_path) as f:
        return json.load(f)


@click.group()
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without applying them.")
@click.version_option(version="0.1.0", prog_name="mcp-stack")
@click.pass_context
def main(ctx: click.Context, dry_run: bool) -> None:
    """mcp-stack - A package manager for MCP servers.

    Install, configure, and manage MCP servers across Claude Desktop,
    Cursor, and Windsurf with a single command.
    """
    ctx.ensure_object(dict)
    ctx.obj["dry_run"] = dry_run


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------


@main.command()
@click.argument("server_name")
@click.option(
    "--client",
    "clients",
    multiple=True,
    type=click.Choice(["claude", "cursor", "windsurf"]),
    help="Target specific client(s). Defaults to all.",
)
@click.pass_context
def install(ctx: click.Context, server_name: str, clients: tuple) -> None:
    """Install an MCP server and configure it for your clients."""
    dry_run: bool = ctx.obj["dry_run"]
    console = _console()

    registry = Registry()
    server = registry.get_server(server_name)

    if not server:
        console.print(f"[red]Error:[/red] Server '{server_name}' not found in registry.")
        console.print(f"Run [bold]mcp-stack search {server_name}[/bold] to find available servers.")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]{server['name']}[/bold]\n{server['description']}",
            title="Installing MCP Server",
            border_style="blue",
        )
    )

    # --- Collect environment variable values ---
    env_values: dict = {}
    for env_var in server.get("env", []):
        if not env_var.get("required"):
            continue
        if dry_run:
            console.print(f"[yellow][dry-run][/yellow] Would prompt for: {env_var['name']}")
        else:
            hide = any(
                kw in env_var["name"]
                for kw in ("TOKEN", "KEY", "SECRET", "PASSWORD", "PASS")
            )
            suffix = " (characters hidden)" if hide else ""
            value = click.prompt(
                f"  {env_var['name']}{suffix}",
                hide_input=hide,
                prompt_suffix=": ",
            )
            env_values[env_var["name"]] = value

    # --- Collect arg-level values (e.g. directory paths) ---
    arg_values: dict = {}
    for ap in server.get("arg_prompts", []):
        if not ap.get("required"):
            continue
        if dry_run:
            console.print(
                f"[yellow][dry-run][/yellow] Would prompt for: {ap['name']} ({ap['description']})"
            )
        else:
            value = click.prompt(f"  {ap['description']}", prompt_suffix=": ")
            key = ap["placeholder"].strip("{}")
            arg_values[key] = value

    config_manager = ConfigManager()
    all_clients = config_manager.get_client_configs()
    target_clients = list(clients) if clients else list(all_clients.keys())

    installer = Installer(dry_run=dry_run)

    if dry_run:
        console.print(
            f"\n[yellow][dry-run][/yellow] Would install: [bold]{server['package']}[/bold]"
            f" (via {server['command']}, auto-downloaded on first use)"
        )
        for client_name in target_clients:
            if client_name in all_clients:
                path = all_clients[client_name]["path"]
                console.print(
                    f"[yellow][dry-run][/yellow] Would write config for"
                    f" [bold]{server['name']}[/bold] to: {path}"
                )
        return

    # --- Verify the runtime is available ---
    success = installer.install_package(server["package"], command=server["command"])
    if not success:
        cmd = server["command"]
        hint = _RUNTIME_INSTALL_HINTS.get(cmd, f"'{cmd}' not found in PATH.")
        console.print(f"[red]Error:[/red] {hint}")
        sys.exit(1)

    server_config = installer.build_server_config(
        server,
        env_values=env_values or None,
        arg_values=arg_values or None,
    )
    written_to = []
    for client_name in target_clients:
        if client_name in all_clients:
            config_path = all_clients[client_name]["path"]
            config_manager.add_server(config_path, server["name"], server_config)
            written_to.append(all_clients[client_name]["name"])

    console.print(f"\n[green]✓[/green] Configured [bold]{server['name']}[/bold]")
    if written_to:
        console.print(f"  Written to: {', '.join(written_to)}")
    console.print(
        "\n[dim]The server package is downloaded automatically on first use.[/dim]"
        "\n[dim]Restart your client(s) to activate the server.[/dim]"
    )


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@main.command()
@click.argument("query", required=False, default="")
def search(query: str) -> None:
    """Search for MCP servers in the registry."""
    console = _console()
    registry = Registry()
    results = registry.search(query)

    if not results:
        console.print(f"No servers found matching '[bold]{query}[/bold]'.")
        return

    table = Table(title="MCP Server Registry", show_header=True, header_style="bold blue")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description")
    table.add_column("Package", style="dim")

    for s in results:
        table.add_row(s["name"], s["description"], s["package"])

    console.print(table)
    console.print(
        f"\n[dim]Found {len(results)} server(s). Use [bold]mcp-stack info <name>[/bold] for details.[/dim]"
    )


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------


@main.command()
@click.argument("server_name")
def info(server_name: str) -> None:
    """Show detailed information about an MCP server."""
    console = _console()
    registry = Registry()
    server = registry.get_server(server_name)

    if not server:
        console.print(f"[red]Error:[/red] Server '{server_name}' not found.")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold cyan]{server['name']}[/bold cyan]\n{server['description']}",
            title="MCP Server Info",
            border_style="blue",
        )
    )

    console.print(f"[bold]Package:[/bold]  {server['package']}")
    console.print(f"[bold]Command:[/bold]  {server['command']} {' '.join(server['args'])}")

    if server.get("homepage"):
        console.print(f"[bold]Homepage:[/bold] {server['homepage']}")

    if server.get("tags"):
        console.print(f"[bold]Tags:[/bold]     {', '.join(server['tags'])}")

    if server.get("notes"):
        console.print(f"\n[yellow]Note:[/yellow] {server['notes']}")

    env_vars = server.get("env", [])
    arg_prompts = server.get("arg_prompts", [])

    if env_vars or arg_prompts:
        console.print("\n[bold]Required inputs:[/bold]")
        for ev in env_vars:
            req = "[red]required[/red]" if ev.get("required") else "[dim]optional[/dim]"
            console.print(f"  • {ev['name']} ({req}) - {ev['description']}")
        for ap in arg_prompts:
            req = "[red]required[/red]" if ap.get("required") else "[dim]optional[/dim]"
            console.print(f"  • {ap['name']} ({req}) - {ap['description']}")
    else:
        console.print("\n[dim]No inputs required.[/dim]")


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


@main.command("list")
@click.option(
    "--client",
    type=click.Choice(["claude", "cursor", "windsurf"]),
    default="claude",
    show_default=True,
    help="Which client to list servers for.",
)
def list_servers(client: str) -> None:
    """List installed MCP servers."""
    console = _console()
    config_manager = ConfigManager()
    client_configs = config_manager.get_client_configs()

    config_path = client_configs[client]["path"]
    installed = config_manager.get_installed_servers(config_path)

    if not installed:
        console.print(
            f"No MCP servers installed for [bold]{client_configs[client]['name']}[/bold]."
        )
        console.print("Run [bold]mcp-stack install <server>[/bold] to get started.")
        return

    table = Table(
        title=f"Installed Servers - {client_configs[client]['name']}",
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Name", style="cyan")
    table.add_column("Command")

    for name, cfg in installed.items():
        cmd = f"{cfg.get('command', 'npx')} {' '.join(cfg.get('args', []))}"
        table.add_row(name, cmd.strip())

    console.print(table)


# ---------------------------------------------------------------------------
# uninstall
# ---------------------------------------------------------------------------


@main.command()
@click.argument("server_name")
@click.option(
    "--client",
    "clients",
    multiple=True,
    type=click.Choice(["claude", "cursor", "windsurf"]),
    help="Target specific client(s). Defaults to all.",
)
@click.pass_context
def uninstall(ctx: click.Context, server_name: str, clients: tuple) -> None:
    """Uninstall an MCP server and remove its configuration."""
    dry_run: bool = ctx.obj["dry_run"]
    console = _console()

    config_manager = ConfigManager()
    all_clients = config_manager.get_client_configs()
    target_clients = list(clients) if clients else list(all_clients.keys())

    if dry_run:
        for client_name in target_clients:
            if client_name in all_clients:
                path = all_clients[client_name]["path"]
                console.print(
                    f"[yellow][dry-run][/yellow] Would remove '{server_name}'"
                    f" from {all_clients[client_name]['name']} ({path})"
                )
        return

    removed_from = []
    for client_name in target_clients:
        if client_name in all_clients:
            config_path = all_clients[client_name]["path"]
            if config_manager.remove_server(config_path, server_name):
                removed_from.append(all_clients[client_name]["name"])

    if removed_from:
        console.print(
            f"[green]✓[/green] Removed [bold]{server_name}[/bold] from: {', '.join(removed_from)}"
        )
        console.print("\n[dim]Restart your client(s) to deactivate the server.[/dim]")
    else:
        console.print(
            f"[yellow]Warning:[/yellow] '{server_name}' was not found in any client config."
        )


# ---------------------------------------------------------------------------
# clients
# ---------------------------------------------------------------------------


@main.command()
def clients() -> None:
    """List supported MCP clients and their config file locations."""
    console = _console()
    config_manager = ConfigManager()
    client_configs = config_manager.get_client_configs()

    table = Table(
        title="Supported MCP Clients", show_header=True, header_style="bold blue"
    )
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Client Name")
    table.add_column("Config Path")
    table.add_column("Status")

    for client_id, client_info in client_configs.items():
        path = client_info["path"]
        status = "[green]found[/green]" if path.exists() else "[dim]not found[/dim]"
        table.add_row(client_id, client_info["name"], str(path), status)

    console.print(table)


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


@main.command()
@click.argument("server_name")
@click.option(
    "--client",
    default="claude",
    type=click.Choice(["claude", "cursor", "windsurf"]),
    show_default=True,
    help="Which client config to read env vars from.",
)
def run(server_name: str, client: str) -> None:
    """Run an MCP server directly (useful for testing)."""
    console = _console()
    registry = Registry()
    server = registry.get_server(server_name)

    if not server:
        console.print(f"[red]Error:[/red] Server '{server_name}' not found in registry.")
        sys.exit(1)

    config_manager = ConfigManager()
    client_configs = config_manager.get_client_configs()

    env_values: dict = {}
    if client in client_configs:
        config_path = client_configs[client]["path"]
        installed = config_manager.get_installed_servers(config_path)
        if server_name in installed:
            env_values = installed[server_name].get("env", {})

    cmd = [server["command"]] + server["args"]
    console.print(f"[dim]Running:[/dim] {' '.join(cmd)}")

    env = os.environ.copy()
    env.update(env_values)

    try:
        subprocess.run(cmd, env=env, check=False)
    except KeyboardInterrupt:
        console.print("\n[dim]Server stopped.[/dim]")
    except FileNotFoundError:
        cmd_name = server["command"]
        hint = _RUNTIME_INSTALL_HINTS.get(cmd_name, f"'{cmd_name}' not found in PATH.")
        console.print(f"[red]Error:[/red] {hint}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


@main.command()
@click.argument("server_name", required=False, default=None)
@click.option(
    "--client",
    default="claude",
    type=click.Choice(["claude", "cursor", "windsurf"]),
    show_default=True,
    help="Which client config to check for installed servers.",
)
@click.pass_context
def update(ctx: click.Context, server_name: str | None, client: str) -> None:
    """Update installed MCP server(s) to the latest version."""
    dry_run: bool = ctx.obj["dry_run"]
    console = _console()

    registry = Registry()
    config_manager = ConfigManager()
    client_configs = config_manager.get_client_configs()

    config_path = client_configs[client]["path"]
    installed = config_manager.get_installed_servers(config_path)

    if server_name:
        if server_name not in installed:
            console.print(f"[yellow]Warning:[/yellow] '{server_name}' is not installed.")
            return
        servers_to_update = {server_name: installed[server_name]}
    else:
        servers_to_update = installed

    if not servers_to_update:
        console.print("No servers installed to update.")
        return

    for name in servers_to_update:
        server_def = registry.get_server(name)
        if not server_def:
            console.print(f"[dim]Skipping '{name}' - not in registry.[/dim]")
            continue

        cmd = server_def["command"]
        package = server_def["package"]

        if cmd == "uvx":
            if dry_run:
                console.print(
                    f"[yellow][dry-run][/yellow] Would update: [bold]{package}[/bold] via uvx"
                )
            else:
                console.print(f"Updating [bold]{package}[/bold] via uvx...")
                result = subprocess.run(
                    ["uvx", "--reinstall", package],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    console.print(f"[green]✓[/green] Updated {name}")
                else:
                    console.print(f"[red]Failed to update {name}:[/red] {result.stderr}")
        else:
            if dry_run:
                console.print(
                    f"[yellow][dry-run][/yellow] Would update: [bold]{package}[/bold] via npx"
                )
            else:
                console.print(
                    f"[green]✓[/green] {name} uses npx — latest version is fetched automatically on each run."
                )


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


@main.command()
def doctor() -> None:
    """Check system health: runtimes, client configs, and installed servers."""
    import shutil as _shutil

    console = _console()

    table = Table(title="mcp-stack Doctor", show_header=True, header_style="bold blue")
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Detail", style="dim")

    all_ok = True

    def _row(name: str, ok: bool, detail: str = "") -> None:
        nonlocal all_ok
        if not ok:
            all_ok = False
        status = "[green]✓ ok[/green]" if ok else "[red]✗ fail[/red]"
        table.add_row(name, status, detail)

    # --- Runtime checks ---
    for runtime, label, hint in [
        ("node", "Node.js", "install from https://nodejs.org"),
        ("npx", "npx", "comes with Node.js"),
        ("uvx", "uvx (uv)", "optional — needed for git/time servers; https://docs.astral.sh/uv/"),
    ]:
        path = _shutil.which(runtime)
        if path:
            try:
                v = subprocess.run([runtime, "--version"], capture_output=True, text=True, timeout=5)
                _row(label, True, v.stdout.strip() or v.stderr.strip())
            except Exception:
                _row(label, True, path)
        else:
            _row(label, runtime == "uvx", hint)  # uvx missing is a warning, not fatal

    # --- Client config checks ---
    config_manager = ConfigManager()
    for client_id, client_info in config_manager.get_client_configs().items():
        path = client_info["path"]
        if not path.exists():
            _row(f"{client_info['name']} config", True, "not found (created on first install)")
            continue
        try:
            config_manager.read_config(path)
            _row(f"{client_info['name']} config", True, str(path))
        except Exception as e:
            _row(f"{client_info['name']} config", False, f"invalid JSON: {e}")

    # --- Installed server checks (Claude Desktop) ---
    registry = Registry()
    claude_path = config_manager.get_client_configs()["claude"]["path"]
    installed = config_manager.get_installed_servers(claude_path)

    for name, cfg in installed.items():
        cmd = cfg.get("command", "npx")
        runtime_ok = _shutil.which(cmd) is not None
        in_registry = registry.get_server(name) is not None
        ok = runtime_ok and in_registry
        details = []
        if not in_registry:
            details.append("not in registry")
        if not runtime_ok:
            details.append(f"'{cmd}' not in PATH")
        _row(f"server: {name}", ok, ", ".join(details) or f"via {cmd}")

    console.print(table)
    if all_ok:
        console.print("\n[green]All checks passed.[/green]")
    else:
        console.print("\n[yellow]Some checks failed — see details above.[/yellow]")


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------


@main.group()
def profile() -> None:
    """Manage server profiles — install curated sets of servers at once."""
    pass


@profile.command("list")
def profile_list() -> None:
    """List all available server profiles."""
    console = _console()
    profiles = _load_profiles()

    table = Table(title="Available Profiles", show_header=True, header_style="bold blue")
    table.add_column("Profile", style="cyan", no_wrap=True)
    table.add_column("Description")
    table.add_column("Servers", style="dim")

    for name, info in profiles.items():
        table.add_row(name, info["description"], ", ".join(info["servers"]))

    console.print(table)
    console.print(
        "\n[dim]Use [bold]mcp-stack profile install <name>[/bold] to install a profile.[/dim]"
    )


@profile.command("show")
@click.argument("profile_name")
def profile_show(profile_name: str) -> None:
    """Show servers included in a profile."""
    console = _console()
    profiles = _load_profiles()

    if profile_name not in profiles:
        console.print(f"[red]Error:[/red] Profile '{profile_name}' not found.")
        console.print("Run [bold]mcp-stack profile list[/bold] to see available profiles.")
        sys.exit(1)

    p = profiles[profile_name]
    registry = Registry()

    console.print(
        Panel(
            f"[bold]{profile_name}[/bold]\n{p['description']}",
            title="Profile",
            border_style="blue",
        )
    )

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Server", style="cyan")
    table.add_column("Description")
    table.add_column("Required inputs", style="dim")

    for server_name in p["servers"]:
        server = registry.get_server(server_name)
        if server:
            required = [e["name"] for e in server.get("env", []) if e.get("required")]
            required += [ap["name"] for ap in server.get("arg_prompts", []) if ap.get("required")]
            table.add_row(
                server_name,
                server["description"],
                ", ".join(required) if required else "[dim]none[/dim]",
            )

    console.print(table)


@profile.command("install")
@click.argument("profile_name")
@click.option(
    "--client",
    "clients",
    multiple=True,
    type=click.Choice(["claude", "cursor", "windsurf"]),
    help="Target specific client(s). Defaults to all.",
)
@click.pass_context
def profile_install(ctx: click.Context, profile_name: str, clients: tuple) -> None:
    """Install all servers in a profile."""
    console = _console()
    profiles = _load_profiles()

    if profile_name not in profiles:
        console.print(f"[red]Error:[/red] Profile '{profile_name}' not found.")
        console.print("Run [bold]mcp-stack profile list[/bold] to see available profiles.")
        sys.exit(1)

    p = profiles[profile_name]
    console.print(
        Panel(
            f"[bold]{profile_name}[/bold] — {p['description']}\n"
            f"Servers: {', '.join(p['servers'])}",
            title="Installing Profile",
            border_style="blue",
        )
    )

    failed = []
    for server_name in p["servers"]:
        console.print(f"\n[cyan]→[/cyan] Installing [bold]{server_name}[/bold]...")
        try:
            ctx.invoke(install, server_name=server_name, clients=clients)
        except SystemExit:
            failed.append(server_name)
            console.print(f"  [yellow]Skipped {server_name}.[/yellow]")

    console.print(f"\n[green]✓[/green] Profile [bold]{profile_name}[/bold] complete.")
    if failed:
        console.print(f"  [yellow]Skipped:[/yellow] {', '.join(failed)}")


# ---------------------------------------------------------------------------
# backup
# ---------------------------------------------------------------------------


@main.command()
@click.option("--list", "show_list", is_flag=True, help="List available backups.")
def backup(show_list: bool) -> None:
    """Backup all client MCP configs to ~/.mcp-stack/backups/."""
    console = _console()
    config_manager = ConfigManager()

    if show_list:
        backups = config_manager.list_backups()
        if not backups:
            console.print("[dim]No backups found.[/dim]")
            return
        table = Table(title="Available Backups", show_header=True, header_style="bold blue")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Path", style="dim")
        for b in backups:
            table.add_row(b.name, str(b))
        console.print(table)
        return

    backup_dir, backed_up = config_manager.backup()
    if not backed_up:
        console.print("[yellow]No config files found to back up.[/yellow]")
        return

    console.print(f"[green]✓[/green] Backed up: {', '.join(backed_up)}")
    console.print(f"  Saved to: [dim]{backup_dir}[/dim]")


# ---------------------------------------------------------------------------
# restore
# ---------------------------------------------------------------------------


@main.command()
@click.argument("timestamp", required=False, default=None)
def restore(timestamp: str | None) -> None:
    """Restore client configs from a backup. Use 'mcp-stack backup --list' to see backups."""
    console = _console()
    config_manager = ConfigManager()
    backups = config_manager.list_backups()

    if not backups:
        console.print("[yellow]No backups found.[/yellow] Run [bold]mcp-stack backup[/bold] first.")
        return

    if timestamp:
        backup_dir = next((b for b in backups if b.name == timestamp), None)
        if not backup_dir:
            console.print(f"[red]Error:[/red] Backup '{timestamp}' not found.")
            console.print("Run [bold]mcp-stack backup --list[/bold] to see available backups.")
            sys.exit(1)
    else:
        backup_dir = backups[0]
        console.print(f"[dim]Using latest backup: {backup_dir.name}[/dim]")

    restored = config_manager.restore(backup_dir)
    if restored:
        console.print(f"[green]✓[/green] Restored: {', '.join(restored)}")
        console.print("[dim]Restart your client(s) to load the restored config.[/dim]")
    else:
        console.print("[yellow]No configs were restored from that backup.[/yellow]")


# ---------------------------------------------------------------------------
# registry (group)
# ---------------------------------------------------------------------------


@main.group("registry")
def registry_group() -> None:
    """Manage the mcp-stack server registry."""
    pass


@registry_group.command("update")
def registry_update() -> None:
    """Fetch the latest server list from GitHub and update the local registry."""
    console = _console()
    registry = Registry()

    console.print("[dim]Fetching registry from GitHub...[/dim]")
    try:
        servers = registry.fetch_remote(REGISTRY_UPDATE_URL)
        count = registry.save_custom(servers)
        console.print(f"[green]✓[/green] Registry updated: {count} server(s) loaded.")
        console.print("[dim]Run [bold]mcp-stack search[/bold] to see all available servers.[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to fetch registry: {e}")
        sys.exit(1)


@registry_group.command("add")
@click.argument("url")
def registry_add(url: str) -> None:
    """Add servers from a custom registry URL."""
    console = _console()
    registry = Registry()

    console.print(f"[dim]Fetching registry from {url}...[/dim]")
    try:
        servers = registry.fetch_remote(url)
        if not servers:
            console.print("[yellow]No servers found at that URL.[/yellow]")
            return
        count = registry.save_custom(servers)
        console.print(f"[green]✓[/green] Added {count} server(s) to local registry:")
        for s in servers:
            console.print(f"  • [cyan]{s['name']}[/cyan] — {s.get('description', '')}")
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to fetch registry: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


@main.command()
@click.option(
    "--client",
    default="claude",
    type=click.Choice(["claude", "cursor", "windsurf"]),
    show_default=True,
    help="Which client to export servers from.",
)
@click.option("--output", "-o", default=None, help="Output file path (default: print to stdout).")
def export(client: str, output: str | None) -> None:
    """Export installed MCP servers as a shareable JSON file."""
    console = _console()
    config_manager = ConfigManager()
    client_configs = config_manager.get_client_configs()

    config_path = client_configs[client]["path"]
    installed = config_manager.get_installed_servers(config_path)

    if not installed:
        console.print(
            f"[yellow]No servers installed for {client_configs[client]['name']}.[/yellow]"
        )
        return

    export_data = {
        "mcp_ctl_export": "1.0.0",
        "exported_at": datetime.now().isoformat(),
        "source_client": client,
        "servers": installed,
    }

    export_json = json.dumps(export_data, indent=2)

    if output:
        Path(output).write_text(export_json)
        console.print(
            f"[green]✓[/green] Exported {len(installed)} server(s) to [bold]{output}[/bold]"
        )
    else:
        print(export_json)
