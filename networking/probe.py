"""Look up a name (DNS), then open a TCP connection to it, and time both.

    python3 probe.py example.com 443
    python3 probe.py localhost 22

Standard library only. It does not send any data: it only opens the connection
(the TCP three-way handshake) and closes it again.

Exit codes: 0 connected, 1 could not connect, 2 the name did not resolve.
"""

import argparse
import socket
import sys
import time
from dataclasses import dataclass


@dataclass
class Result:
    host: str
    port: int
    addresses: list  # every address DNS gave us, as strings
    dns_ms: float
    connected_to: str | None = None
    connect_ms: float | None = None
    error: str | None = None


def resolve(host: str, port: int) -> tuple[list, float]:
    """Ask the system resolver for the host's TCP addresses. Returns (addrinfo list, milliseconds)."""
    start = time.perf_counter()
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    elapsed = (time.perf_counter() - start) * 1000
    return infos, elapsed


def probe(host: str, port: int, timeout: float = 3.0) -> Result:
    """Resolve the name, then try each address in turn until one accepts a TCP connection.

    Raises socket.gaierror if the name does not resolve.
    """
    infos, dns_ms = resolve(host, port)
    # The same address can come back more than once; keep the first of each, in order.
    seen = []
    for info in infos:
        if info[4] not in [s[4] for s in seen]:
            seen.append(info)
    result = Result(host, port, [info[4][0] for info in seen], dns_ms)

    last_error = None
    for family, socktype, proto, _canon, sockaddr in seen:
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(timeout)
        try:
            start = time.perf_counter()
            sock.connect(sockaddr)
            result.connect_ms = (time.perf_counter() - start) * 1000
            result.connected_to = sockaddr[0]
            return result
        except OSError as exc:
            last_error = exc
        finally:
            sock.close()

    result.error = str(last_error) if last_error else "no addresses to try"
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Time a DNS lookup and a TCP connection.")
    parser.add_argument("host", help="a name such as example.com, or an IP address")
    parser.add_argument("port", type=int, help="a TCP port, such as 443 for HTTPS")
    parser.add_argument("--timeout", type=float, default=3.0, help="seconds to wait for each connection (default 3)")
    args = parser.parse_args(argv)

    if not 0 < args.port < 65536:
        parser.error("port must be between 1 and 65535")

    try:
        result = probe(args.host, args.port, args.timeout)
    except socket.gaierror as exc:
        print(f"DNS: could not resolve {args.host!r}: {exc}", file=sys.stderr)
        return 2

    print(f"DNS: {result.host} -> {', '.join(result.addresses)}  ({result.dns_ms:.1f} ms)")
    if result.connected_to is None:
        print(f"TCP: could not connect to port {result.port}: {result.error}", file=sys.stderr)
        return 1
    print(f"TCP: connected to {result.connected_to} port {result.port}  ({result.connect_ms:.1f} ms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
