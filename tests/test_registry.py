import pytest
from mcpx.registry import Registry


def test_load_registry():
    r = Registry()
    assert r is not None


def test_registry_has_15_servers():
    r = Registry()
    assert len(r.all_servers()) == 15


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
    assert "postgres" in names or "sqlite" in names


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
    assert len(names) == 15
    assert "github" in names
    assert "filesystem" in names
    assert "brave-search" in names
