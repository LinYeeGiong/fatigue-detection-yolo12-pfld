import os

from server.entrypoint import server_host


def test_server_host_defaults_to_localhost_for_desktop(monkeypatch):
    monkeypatch.delenv("HOST", raising=False)
    assert server_host() == "127.0.0.1"


def test_server_host_can_bind_all_interfaces_for_container(monkeypatch):
    monkeypatch.setenv("HOST", "0.0.0.0")
    assert server_host() == "0.0.0.0"
