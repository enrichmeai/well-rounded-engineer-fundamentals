"""Tests for probe.py. They use localhost only, so they need no internet connection."""

import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import probe  # noqa: E402


@pytest.fixture
def listening_port():
    """A real TCP listener on 127.0.0.1, on a port the OS picks."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen()
    yield server.getsockname()[1]
    server.close()


@pytest.fixture
def closed_port():
    """A port nothing listens on: bind to get a free number, then let it go."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_connects_to_a_listening_port(listening_port):
    result = probe.probe("127.0.0.1", listening_port)
    assert result.connected_to == "127.0.0.1"
    assert result.connect_ms is not None and result.connect_ms >= 0
    assert result.dns_ms >= 0
    assert result.error is None


def test_localhost_resolves(listening_port):
    result = probe.probe("localhost", listening_port)
    assert result.addresses  # at least one address
    assert result.connected_to == "127.0.0.1"


def test_closed_port_reports_an_error(closed_port):
    result = probe.probe("127.0.0.1", closed_port, timeout=1)
    assert result.connected_to is None
    assert result.error


def test_main_exit_0_when_connected(listening_port, capsys):
    assert probe.main(["127.0.0.1", str(listening_port)]) == 0
    out = capsys.readouterr().out
    assert "DNS: 127.0.0.1 -> 127.0.0.1" in out
    assert f"TCP: connected to 127.0.0.1 port {listening_port}" in out


def test_main_exit_1_when_refused(closed_port, capsys):
    assert probe.main(["127.0.0.1", str(closed_port), "--timeout", "1"]) == 1
    assert "could not connect" in capsys.readouterr().err


def test_main_exit_2_when_name_does_not_resolve(monkeypatch, capsys):
    # Pretend the resolver says "no such name", so the test does not depend on real DNS.
    def fake_getaddrinfo(*args, **kwargs):
        raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    assert probe.main(["no-such-name.invalid", "80"]) == 2
    assert "could not resolve" in capsys.readouterr().err


def test_bad_port_is_a_usage_error():
    with pytest.raises(SystemExit) as exc:
        probe.main(["localhost", "70000"])
    assert exc.value.code == 2
