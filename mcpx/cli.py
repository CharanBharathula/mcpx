import os
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import ConfigManager
from .installer import Installer
from .registry import Registry

_RUNTIME_INSTALL_HINTS = {
    "npx": "Node.js not found. Install from https://nodejs.org",
    "node": "Node.js not found. Install from https://nodejs.org",
    "uvx": "uv not found. Install from https://docs.astral.sh/uv/",
}


def _console() -> Console:
    """Return a Console writing to current sys.stdout (CliRunner-compatible)."""
    return Console(highlight=False)


@click.group()
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without applying them.")
@click.version_option(version="0.1.0", prog_name="mcpx")
@click.pass_context
def main(ctx: click.Context, dry_run: bool) -> None:
    """mcpx - A package manager for MCP servers.

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
        console.print(f"Run [bold]mcpx search {server_name}[/bold] to find available servers.")
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
        f"\n[dim]Found {len(results)} server(s). Use [bold]mcpx info <name>[/bold] for details.[/dim]"
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
        console.print("Run [bold]mcpx install <server>[/bold] to get started.")
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
            # npx-based servers download the latest version automatically on each run
            if dry_run:
                console.print(
                    f"[yellow][dry-run][/yellow] Would update: [bold]{package}[/bold] via npx"
                )
            else:
                console.print(
                    f"[green]✓[/green] {name} uses npx - latest version is fetched automatically on each run."
                )
