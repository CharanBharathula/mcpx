import pytest
from mcp_stack.registry import Registry

ORIGINAL_15 = [
    "github", "filesystem", "fetch", "memory", "postgres", "sqlite",
    "brave-search", "puppeteer", "slack", "git", "time",
    "sequential-thinking", "google-maps", "gitlab", "everything",
]

NEW_SERVERS = [
    "playwright", "sentry", "kubernetes", "docker", "notion", "azure",
    "hubspot", "figma", "supabase", "aws-kb-retrieval", "cloudflare",
    "exa", "stripe", "obsidian", "mongodb", "atlassian",
]


def test_load_registry():
    r = Registry()
    assert r is not None


def test_registry_has_31_servers():
    r = Registry()
    assert len(r.all_servers()) == 31


def test_get_server_github():
    r = Registry()
    server = r.get_server("github")
    assert server is not None
    assert server["name"] == "github"


def test_get_server_nonexistent():
    r = Registry()
    server = r.get_server("nonexistent-xyz-server")
    assert server is None


def test_search_by_name():
    r = Registry()
    results = r.search("github")
    names = [s["name"] for s in results]
    assert "github" in names


def test_search_by_tag():
    r = Registry()
    results = r.search("database")
    names = [s["name"] for s in results]
    assert any(n in names for n in ("postgres", "sqlite", "mongodb"))


def test_search_no_results():
    r = Registry()
    results = r.search("zzz-nothing-matches-zzz")
    assert results == []


def test_server_required_fields():
    r = Registry()
    for server in r.all_servers():
        assert "name" in server
        assert "description" in server
        assert "package" in server
        assert "command" in server
        assert "args" in server


def test_github_env_required():
    r = Registry()
    server = r.get_server("github")
    env_names = [e["name"] for e in server["env"]]
    assert "GITHUB_PERSONAL_ACCESS_TOKEN" in env_names


def test_list_server_names():
    r = Registry()
    names = r.list_names()
    assert isinstance(names, list)
    assert len(names) == 31
    assert "github" in names
    assert "filesystem" in names
    assert "brave-search" in names


def test_all_original_15_servers_present():
    r = Registry()
    names = r.list_names()
    for name in ORIGINAL_15:
        assert name in names, f"Original server '{name}' missing from registry"


def test_all_new_16_servers_present():
    r = Registry()
    names = r.list_names()
    for name in NEW_SERVERS:
        assert name in names, f"New server '{name}' missing from registry"


def test_new_servers_have_required_fields():
    r = Registry()
    for name in NEW_SERVERS:
        server = r.get_server(name)
        assert server is not None
        assert server["command"] in ("npx", "uvx", "node")
        assert isinstance(server["args"], list)


def test_servers_with_no_config_have_empty_prompts():
    r = Registry()
    for name in ("memory", "fetch", "playwright", "docker", "kubernetes"):
        server = r.get_server(name)
        assert server["env"] == []
        assert server.get("arg_prompts", []) == []


def test_notion_requires_token():
    r = Registry()
    server = r.get_server("notion")
    env_names = [e["name"] for e in server["env"]]
    assert "NOTION_TOKEN" in env_names


def test_stripe_requires_secret_key():
    r = Registry()
    server = r.get_server("stripe")
    env_names = [e["name"] for e in server["env"]]
    assert "STRIPE_SECRET_KEY" in env_names


def test_aws_kb_retrieval_requires_aws_creds():
    r = Registry()
    server = r.get_server("aws-kb-retrieval")
    env_names = [e["name"] for e in server["env"]]
    assert "AWS_ACCESS_KEY_ID" in env_names
    assert "AWS_SECRET_ACCESS_KEY" in env_names
    assert "AWS_REGION" in env_names


def test_filesystem_has_arg_prompt():
    r = Registry()
    server = r.get_server("filesystem")
    placeholders = [ap["placeholder"] for ap in server.get("arg_prompts", [])]
    assert "{allowed_dir}" in placeholders


def test_supabase_has_access_token_arg_prompt():
    r = Registry()
    server = r.get_server("supabase")
    placeholders = [ap["placeholder"] for ap in server.get("arg_prompts", [])]
    assert "{access_token}" in placeholders


def test_sentry_has_access_token_arg_prompt():
    r = Registry()
    server = r.get_server("sentry")
    placeholders = [ap["placeholder"] for ap in server.get("arg_prompts", [])]
    assert "{access_token}" in placeholders


def test_obsidian_has_vault_path_arg_prompt():
    r = Registry()
    server = r.get_server("obsidian")
    placeholders = [ap["placeholder"] for ap in server.get("arg_prompts", [])]
    assert "{vault_path}" in placeholders


def test_servers_with_notes_have_string_notes():
    r = Registry()
    for server in r.all_servers():
        if "notes" in server:
            assert isinstance(server["notes"], str)
            assert len(server["notes"]) > 0
