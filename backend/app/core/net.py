from typing import Optional

from fastapi import Request

# An IPv6 address maxes out at 45 characters (the IPv4-mapped form), which is
# what users.last_ip is sized for. Anything longer is malformed or spoofed.
MAX_IP_LENGTH = 45


def get_client_ip(request: Request) -> Optional[str]:
    """Best-effort client IP for audit/abuse metadata.

    Railway (like most PaaS) terminates TLS at a proxy, so `request.client.host`
    is the proxy's address rather than the user's — X-Forwarded-For has to win.
    That header is client-controllable and only trustworthy because a trusted
    proxy rewrites it, so the value is treated as advisory: it is never used to
    identify a guest, only recorded alongside one.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Left-most entry is the original client; the rest are proxy hops.
        candidate = forwarded.split(",")[0].strip()
        if candidate and len(candidate) <= MAX_IP_LENGTH:
            return candidate

    if request.client and request.client.host:
        return request.client.host[:MAX_IP_LENGTH]

    return None
